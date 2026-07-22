"""Deterministic data-quality checks for generated table records."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

from docnexus.ai.table_engine.core.models import (
    EvidencePack,
    StructuredRecord,
    TaskSpec,
    TemplateSpec,
    VerificationCheck,
)

IDENTITY_TOKENS = ("日期", "时间", "城市", "国家", "地区", "省份", "名称", "编号", "id", "date", "time", "city", "country")
UNIT_PATTERN = re.compile(r"(?:%|％|亿元|万元|元|万人|人|万吨|吨|公里|千米|km|kg|万|亿)$", re.IGNORECASE)


def _normalize(value: object) -> str:
    return "".join(str(value or "").strip().lower().split())


def _field_names(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(field) for field in value if field not in (None, "")]
    return [str(value)] if value not in (None, "") else []


def _number(value: object) -> Decimal | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    if not match:
        return None
    try:
        return Decimal(match.group(0))
    except InvalidOperation:
        return None


def _identity_fields(template_spec: TemplateSpec, target_table_id: str) -> list[str]:
    table = next((item for item in template_spec.target_tables if item.target_table_id == target_table_id), None)
    if table is None:
        return []
    fields = [field.field_name for field in table.schema]
    identities = [field for field in fields if any(token in _normalize(field) for token in IDENTITY_TOKENS)]
    return identities[:3]


def _duplicate_identity_check(template_spec: TemplateSpec, records: list[StructuredRecord]) -> VerificationCheck:
    duplicates: list[str] = []
    by_table: dict[str, list[StructuredRecord]] = defaultdict(list)
    for record in records:
        by_table[record.target_table_id].append(record)
    for table_id, members in by_table.items():
        fields = _identity_fields(template_spec, table_id)
        if not fields:
            continue
        seen: dict[tuple[str, ...], str] = {}
        for record in members:
            key = tuple(_normalize(record.values.get(field)) for field in fields)
            if not all(key):
                continue
            if key in seen:
                duplicates.extend([seen[key], record.record_id])
            else:
                seen[key] = record.record_id
    duplicates = list(dict.fromkeys(duplicates))
    return VerificationCheck(
        name="primary_key_uniqueness",
        status="fail" if duplicates else "pass",
        message=("No duplicate record identities detected." if not duplicates else f"Detected {len(duplicates)} record(s) with duplicate identities."),
        related_ids=duplicates[:20],
    )


def _source_conflict_check(evidence_pack: EvidencePack) -> VerificationCheck:
    observations: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for item in evidence_pack.items:
        if item.evidence_type != "row" or not isinstance(item.content, dict):
            continue
        identity_parts = [
            _normalize(value)
            for field, value in item.content.items()
            if any(token in _normalize(field) for token in IDENTITY_TOKENS) and value not in (None, "")
        ]
        if not identity_parts:
            continue
        identity = "|".join(identity_parts)
        for field, value in item.content.items():
            if value in (None, ""):
                continue
            observations[(identity, _normalize(field))][_normalize(value)].add(item.source_doc_id)
    conflicts = []
    for (identity, field), values in observations.items():
        cross_source_values = [value for value, sources in values.items() if sources]
        all_sources = {source for sources in values.values() for source in sources}
        if len(cross_source_values) > 1 and len(all_sources) > 1:
            conflicts.append(f"{identity}:{field}")
    return VerificationCheck(
        name="cross_source_consistency",
        status="warning" if conflicts else "pass",
        message=("No cross-source value conflicts detected." if not conflicts else f"Detected {len(conflicts)} cross-source field conflict(s)."),
        related_ids=conflicts[:20],
    )


def _unit_consistency_check(records: list[StructuredRecord]) -> VerificationCheck:
    units_by_field: dict[str, set[str]] = defaultdict(set)
    for record in records:
        for field, value in record.values.items():
            if value in (None, ""):
                continue
            match = UNIT_PATTERN.search(str(value).strip())
            if match:
                units_by_field[field].add(match.group(0).lower())
    inconsistent = [f"{field}:{','.join(sorted(units))}" for field, units in units_by_field.items() if len(units) > 1]
    return VerificationCheck(
        name="unit_consistency",
        status="warning" if inconsistent else "pass",
        message=("Units are consistent within each output field." if not inconsistent else f"Detected inconsistent units in {len(inconsistent)} field(s)."),
        related_ids=inconsistent[:20],
    )


def _date_continuity_check(task_spec: TaskSpec, records: list[StructuredRecord]) -> VerificationCheck:
    request_text = " ".join(str(constraint.value) for constraint in task_spec.constraints if constraint.kind == "request_text")
    requires_continuity = any(token in request_text.lower() for token in ("连续", "每日", "逐日", "daily", "continuous"))
    gaps: list[str] = []
    if requires_continuity:
        grouped: dict[str, list[date]] = defaultdict(list)
        for record in records:
            date_value = next(
                (value for field, value in record.values.items() if any(token in _normalize(field) for token in ("日期", "date"))),
                None,
            )
            if date_value in (None, ""):
                continue
            try:
                parsed = date.fromisoformat(str(date_value)[:10])
            except ValueError:
                continue
            identity = next(
                (
                    _normalize(value)
                    for field, value in record.values.items()
                    if any(token in _normalize(field) for token in ("城市", "国家", "地区", "city", "country"))
                ),
                "__all__",
            )
            grouped[identity].append(parsed)
        for identity, values in grouped.items():
            ordered = sorted(set(values))
            for previous, current in zip(ordered, ordered[1:]):
                if (current - previous).days > 1:
                    gaps.append(f"{identity}:{previous.isoformat()}..{current.isoformat()}")
    return VerificationCheck(
        name="date_continuity",
        status="warning" if gaps else "pass",
        message=("No required date continuity gaps detected." if not gaps else f"Detected {len(gaps)} date continuity gap(s)."),
        related_ids=gaps[:20],
    )


def _aggregate_reconciliation_check(
    task_spec: TaskSpec,
    evidence_pack: EvidencePack,
    records: list[StructuredRecord],
) -> VerificationCheck:
    issues: list[str] = []
    active_group_fields: list[str] = []
    for operation in task_spec.task_plan.operations if task_spec.task_plan else []:
        if operation.op == "group_by":
            active_group_fields = _field_names(operation.params.get("fields") or operation.params.get("by"))
            continue
        if operation.op != "aggregate":
            continue
        raw_metrics = operation.params.get("metrics") or operation.params.get("aggregations") or []
        metrics = [metric for metric in raw_metrics if isinstance(metric, dict)] if isinstance(raw_metrics, list) else []
        group_fields = operation.params.get("group_by") or operation.params.get("group_fields") or active_group_fields
        groups = _field_names(group_fields)
        allowed_sources = {name for name in operation.inputs if name not in {"source", "records"}}
        rows = [
            item.content
            for item in evidence_pack.items
            if item.evidence_type == "row"
            and isinstance(item.content, dict)
            and (not allowed_sources or item.source_doc_id in allowed_sources)
        ]
        grouped_rows: dict[tuple[str, ...], list[dict[str, object]]] = defaultdict(list)
        for row in rows:
            key = tuple(_normalize(row.get(field)) for field in groups) if groups else ("__all__",)
            grouped_rows[key].append(row)
        output_records = [
            record
            for record in records
            if not operation.target_table_id or record.target_table_id == operation.target_table_id
        ]
        for key, members in grouped_rows.items():
            output = next(
                (
                    record
                    for record in output_records
                    if (tuple(_normalize(record.values.get(field)) for field in groups) if groups else ("__all__",)) == key
                ),
                None,
            )
            if output is None:
                issues.append(f"{operation.operation_id}:{'|'.join(key)}:missing_group")
                continue
            for metric in metrics:
                source_field = str(metric.get("field") or "")
                output_field = str(metric.get("alias") or metric.get("output_field") or source_field)
                function = str(metric.get("function") or metric.get("func") or "sum").lower()
                numbers = [number for number in (_number(member.get(source_field)) for member in members) if number is not None]
                if not numbers:
                    continue
                if function in {"avg", "average", "mean"}:
                    expected = sum(numbers, Decimal("0")) / Decimal(len(numbers))
                elif function == "count":
                    expected = Decimal(len(numbers))
                elif function == "min":
                    expected = min(numbers)
                elif function == "max":
                    expected = max(numbers)
                else:
                    expected = sum(numbers, Decimal("0"))
                actual = _number(output.values.get(output_field))
                if actual is None or abs(actual - expected) > Decimal("0.000001"):
                    issues.append(f"{operation.operation_id}:{'|'.join(key)}:{output_field}")
    return VerificationCheck(
        name="aggregate_reconciliation",
        status="fail" if issues else "pass",
        message=(
            "Aggregate outputs reconcile with available detail evidence."
            if not issues
            else f"Detected {len(issues)} aggregate/detail reconciliation issue(s)."
        ),
        related_ids=issues[:20],
    )


def build_data_quality_checks(
    task_spec: TaskSpec,
    template_spec: TemplateSpec,
    evidence_pack: EvidencePack,
    records: list[StructuredRecord],
) -> list[VerificationCheck]:
    """Build stable, explainable quality checks without invoking an LLM."""
    return [
        _duplicate_identity_check(template_spec, records),
        _source_conflict_check(evidence_pack),
        _unit_consistency_check(records),
        _date_continuity_check(task_spec, records),
        _aggregate_reconciliation_check(task_spec, evidence_pack, records),
    ]
