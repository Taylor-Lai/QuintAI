"""Execute validated TaskPlan operations over structured records."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from statistics import median

from docnexus.ai.table_engine.core.models import StructuredRecord, TaskPlan


@dataclass(slots=True)
class ExecutionResult:
    records: list[StructuredRecord]
    applied_operations: list[str] = field(default_factory=list)
    skipped_operations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    operation_metrics: list[dict[str, object]] = field(default_factory=list)


def plan_for_target_table(plan: TaskPlan | None, target_table_id: str) -> TaskPlan | None:
    """Select operations explicitly assigned to a target table plus compatible global operations."""
    if plan is None:
        return None
    scoped = [
        operation
        for operation in plan.operations
        if operation.target_table_id in {None, target_table_id}
    ]
    scoped_ids = {operation.operation_id for operation in scoped}
    return TaskPlan(
        version=plan.version,
        operations=scoped,
        unresolved=list(plan.unresolved),
        source=plan.source,
        validation_errors=[
            error
            for error in plan.validation_errors
            if not any(
                operation.operation_id in error
                for operation in plan.operations
                if operation.operation_id not in scoped_ids
            )
        ],
        validation_warnings=list(plan.validation_warnings),
    )


def _number(value: object) -> Decimal | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def _value(record: StructuredRecord, field_name: str) -> object:
    if field_name in record.values:
        return record.values[field_name]
    normalized = "".join(str(field_name).lower().split())
    for key, value in record.values.items():
        if "".join(str(key).lower().split()) == normalized:
            return value
    return None


def _compare(value: object, operator: object, expected: object) -> bool:
    normalized_operator = str(operator or "=").lower()
    if normalized_operator == "between" and isinstance(expected, dict):
        current = str(value or "")[:10]
        return str(expected.get("start") or "")[:10] <= current <= str(expected.get("end") or "")[:10]
    left_number, right_number = _number(value), _number(expected)
    if left_number is not None and right_number is not None:
        if normalized_operator in {">", "gt"}:
            return left_number > right_number
        if normalized_operator in {">=", "gte"}:
            return left_number >= right_number
        if normalized_operator in {"<", "lt"}:
            return left_number < right_number
        if normalized_operator in {"<=", "lte"}:
            return left_number <= right_number
        if normalized_operator in {"!=", "ne"}:
            return left_number != right_number
        return left_number == right_number
    left_text, right_text = str(value or "").strip().lower(), str(expected or "").strip().lower()
    if normalized_operator in {">", "gt"}:
        return left_text > right_text
    if normalized_operator in {">=", "gte"}:
        return left_text >= right_text
    if normalized_operator in {"<", "lt"}:
        return left_text < right_text
    if normalized_operator in {"<=", "lte"}:
        return left_text <= right_text
    if normalized_operator in {"!=", "ne"}:
        return left_text != right_text
    if normalized_operator == "in" and isinstance(expected, list):
        return any(left_text == str(item).strip().lower() for item in expected)
    return left_text == right_text


def _conditions(params: dict[str, object]) -> list[dict[str, object]]:
    raw = params.get("conditions")
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if params.get("field"):
        return [{"field": params.get("field"), "operator": params.get("operator"), "value": params.get("value")}]
    return []


def _filter(records: list[StructuredRecord], params: dict[str, object], *, exclude: bool) -> list[StructuredRecord]:
    conditions = _conditions(params)
    if not conditions:
        return records
    selected = []
    for record in records:
        matched = all(
            _compare(_value(record, str(condition.get("field") or "")), condition.get("operator"), condition.get("value"))
            for condition in conditions
        )
        if matched != exclude:
            selected.append(record)
    return selected


def _impute(records: list[StructuredRecord], params: dict[str, object]) -> bool:
    field_name = str(params.get("field") or "")
    group_fields = _field_list(params.get("group_by"))
    if not field_name or not any(field_name in record.values for record in records):
        return False
    groups: dict[tuple[str, ...], list[StructuredRecord]] = {}
    for record in records:
        key = tuple(str(_value(record, str(field)) or "") for field in group_fields) if group_fields else ("__all__",)
        groups.setdefault(key, []).append(record)
    method = str(params.get("method") or params.get("strategy") or "median").lower()
    changed = False
    for group_records in groups.values():
        numbers = [_number(_value(record, field_name)) for record in group_records]
        available = [number for number in numbers if number is not None]
        if not available:
            continue
        replacement = (
            Decimal(str(median(available)))
            if method == "median"
            else sum(available, Decimal("0")) / Decimal(len(available))
        )
        replacement_value: int | float = int(replacement) if replacement == replacement.to_integral_value() else float(replacement)
        for record in group_records:
            if _value(record, field_name) in (None, ""):
                record.values[field_name] = replacement_value
                record.notes.append(f"Imputed '{field_name}' using group {method}.")
                changed = True
    return changed


def _aggregate(
    records: list[StructuredRecord],
    params: dict[str, object],
    group_fields: list[str],
) -> list[StructuredRecord] | None:
    raw_metrics = params.get("metrics") or params.get("aggregations") or []
    metrics = [metric for metric in raw_metrics if isinstance(metric, dict)] if isinstance(raw_metrics, list) else []
    if not metrics:
        return None
    source_fields = [str(metric.get("field") or "") for metric in metrics]
    if not any(_number(_value(record, field_name)) is not None for record in records for field_name in source_fields):
        return None
    grouped: dict[tuple[object, ...], list[StructuredRecord]] = {}
    for record in records:
        key = tuple(_value(record, field_name) for field_name in group_fields) if group_fields else ("__all__",)
        grouped.setdefault(key, []).append(record)
    output: list[StructuredRecord] = []
    for index, (key, members) in enumerate(grouped.items()):
        values = {field_name: key[position] for position, field_name in enumerate(group_fields)}
        sources: dict[str, list[str]] = {}
        for field_name in group_fields:
            evidence_ids = []
            for member in members:
                evidence_ids.extend(member.field_sources.get(field_name, []))
            if evidence_ids:
                sources[field_name] = list(dict.fromkeys(evidence_ids))
        for metric in metrics:
            source_field = str(metric.get("field") or "")
            alias = str(metric.get("alias") or source_field)
            function = str(metric.get("function") or metric.get("func") or "sum").lower()
            numbers = [_number(_value(member, source_field)) for member in members]
            available = [number for number in numbers if number is not None]
            if not available:
                values[alias] = None
                continue
            if function in {"avg", "average", "mean"}:
                result = sum(available, Decimal("0")) / Decimal(len(available))
            elif function == "median":
                result = Decimal(str(median(available)))
            elif function == "min":
                result = min(available)
            elif function == "max":
                result = max(available)
            elif function == "count":
                result = Decimal(len(available))
            else:
                result = sum(available, Decimal("0"))
            values[alias] = int(result) if result == result.to_integral_value() else float(result)
            evidence_ids = []
            for member in members:
                evidence_ids.extend(member.field_sources.get(source_field, []))
            sources[alias] = list(dict.fromkeys(evidence_ids))
        output.append(
            StructuredRecord(
                record_id=f"task-plan-aggregate-{index}",
                target_table_id=members[0].target_table_id,
                values=values,
                field_sources=sources,
                confidence=min((member.confidence for member in members), default=0.0),
                notes=[f"Computed deterministic aggregate for {len(members)} record(s)."],
            )
        )
    return output


def _field_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    if value not in (None, ""):
        return [str(value)]
    return []


UNIT_SCALES = {
    "": Decimal("1"),
    "元": Decimal("1"),
    "万元": Decimal("10000"),
    "亿元": Decimal("100000000"),
    "人": Decimal("1"),
    "万人": Decimal("10000"),
    "吨": Decimal("1"),
    "万吨": Decimal("10000"),
    "米": Decimal("1"),
    "千米": Decimal("1000"),
    "公里": Decimal("1000"),
    "m": Decimal("1"),
    "km": Decimal("1000"),
}


def _normalize_unit(records: list[StructuredRecord], params: dict[str, object]) -> bool:
    field_name = str(params.get("field") or "")
    output_field = str(params.get("output_field") or field_name)
    target_unit = str(params.get("target_unit") or "").lower()
    target_scale = UNIT_SCALES.get(target_unit)
    if not field_name or target_scale is None:
        return False
    changed = False
    for record in records:
        raw_value = _value(record, field_name)
        if raw_value in (None, ""):
            continue
        match = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*([^\d\s]*)\s*", str(raw_value).replace(",", ""))
        if not match:
            continue
        source_unit = match.group(2).lower()
        source_scale = UNIT_SCALES.get(source_unit)
        if source_scale is None:
            continue
        value = Decimal(match.group(1)) * source_scale / target_scale
        record.values[output_field] = int(value) if value == value.to_integral_value() else float(value)
        if record.field_sources.get(field_name):
            record.field_sources[output_field] = list(record.field_sources[field_name])
        record.notes.append(f"Normalized '{field_name}' from '{source_unit}' to '{target_unit}'.")
        changed = True
    return changed


def _join_records(
    left_records: list[StructuredRecord],
    right_records: list[StructuredRecord],
    params: dict[str, object],
) -> tuple[list[StructuredRecord] | None, list[str]]:
    warnings: list[str] = []
    left_fields = _field_list(params.get("left_on") or params.get("on"))
    right_fields = _field_list(params.get("right_on") or params.get("on"))
    raw_keys = params.get("keys")
    if isinstance(raw_keys, list) and raw_keys and not left_fields:
        if all(isinstance(item, str) for item in raw_keys):
            left_fields = right_fields = [str(item) for item in raw_keys]
        elif all(isinstance(item, dict) for item in raw_keys):
            left_fields = [str(item.get("left") or item.get("left_field") or "") for item in raw_keys]
            right_fields = [str(item.get("right") or item.get("right_field") or "") for item in raw_keys]
    if not left_fields or len(left_fields) != len(right_fields):
        return None, warnings

    right_index: dict[tuple[str, ...], list[StructuredRecord]] = {}
    for record in right_records:
        key = tuple(str(_value(record, field) or "").strip().lower() for field in right_fields)
        if all(key):
            right_index.setdefault(key, []).append(record)

    how = str(params.get("how") or "inner").lower()
    if how not in {"inner", "left", "right", "full", "outer"}:
        return None, [f"Unsupported join mode: {how}."]
    suffixes = params.get("suffixes") or ["_left", "_right"]
    right_suffix = str(suffixes[1]) if isinstance(suffixes, list) and len(suffixes) > 1 else "_right"
    joined: list[StructuredRecord] = []
    matched_right_ids: set[str] = set()
    duplicate_left_keys: set[tuple[str, ...]] = set()
    left_key_counts: dict[tuple[str, ...], int] = {}
    for record in left_records:
        key = tuple(str(_value(record, field) or "").strip().lower() for field in left_fields)
        left_key_counts[key] = left_key_counts.get(key, 0) + 1
    duplicate_left_keys.update(key for key, count in left_key_counts.items() if all(key) and count > 1)
    duplicate_right_keys = {key for key, members in right_index.items() if len(members) > 1}
    if duplicate_left_keys & duplicate_right_keys:
        warnings.append("Join contains duplicate keys on both sides; output may have many-to-many expansion.")
    cardinality = str(params.get("validate") or params.get("cardinality") or "").lower()
    cardinality_failed = (
        cardinality in {"one_to_one", "1:1"} and bool(duplicate_left_keys or duplicate_right_keys)
    ) or (
        cardinality in {"one_to_many", "1:m"} and bool(duplicate_left_keys)
    ) or (
        cardinality in {"many_to_one", "m:1"} and bool(duplicate_right_keys)
    )
    if cardinality_failed:
        warnings.append(f"Join cardinality validation failed for '{cardinality}'.")
    for left in left_records:
        key = tuple(str(_value(left, field) or "").strip().lower() for field in left_fields)
        matches: list[StructuredRecord | None] = list(right_index.get(key, []))
        if not matches and how == "left":
            matches = [None]
        for match_index, right in enumerate(matches):
            values = dict(left.values)
            sources = {field_name: list(ids) for field_name, ids in left.field_sources.items()}
            if right is not None:
                matched_right_ids.add(right.record_id)
                for field_name, value in right.values.items():
                    target_name = field_name
                    if target_name in values and field_name not in right_fields and values[target_name] != value:
                        target_name = f"{field_name}{right_suffix}"
                    if target_name not in values or values[target_name] in (None, ""):
                        values[target_name] = value
                    if right.field_sources.get(field_name):
                        sources[target_name] = list(right.field_sources[field_name])
            joined.append(
                StructuredRecord(
                    record_id=f"join:{left.record_id}:{match_index}",
                    target_table_id=left.target_table_id,
                    values=values,
                    field_sources=sources,
                    confidence=min(left.confidence, right.confidence) if right is not None else left.confidence,
                    notes=[*left.notes, *(right.notes if right is not None else []), "Joined deterministic source datasets."],
                )
            )
    if how in {"right", "full", "outer"}:
        target_table_id = left_records[0].target_table_id if left_records else (
            right_records[0].target_table_id if right_records else ""
        )
        for right in right_records:
            if right.record_id in matched_right_ids:
                continue
            joined.append(
                StructuredRecord(
                    record_id=f"join:unmatched-right:{right.record_id}",
                    target_table_id=target_table_id,
                    values=dict(right.values),
                    field_sources={field_name: list(ids) for field_name, ids in right.field_sources.items()},
                    confidence=right.confidence,
                    notes=[*right.notes, "Preserved unmatched right-side record."],
                )
            )
    maximum_growth = params.get("max_growth_factor", 10)
    try:
        growth_limit = float(str(maximum_growth))
    except (TypeError, ValueError):
        growth_limit = 10.0
    baseline = max(len(left_records), len(right_records), 1)
    growth_factor = len(joined) / baseline
    if growth_factor > growth_limit:
        warnings.append(f"Join output expanded {growth_factor:.2f}x, exceeding configured limit {growth_limit:.2f}x.")
    return joined, warnings


def _sort_records(records: list[StructuredRecord], params: dict[str, object]) -> list[StructuredRecord] | None:
    raw_keys = params.get("keys")
    keys: list[tuple[str, bool]] = []
    if isinstance(raw_keys, list):
        for item in raw_keys:
            if isinstance(item, dict) and (item.get("field") or item.get("by")):
                keys.append(
                    (
                        str(item.get("field") or item.get("by")),
                        str(item.get("order") or "asc").lower() == "desc",
                    )
                )
            elif item not in (None, ""):
                keys.append((str(item), False))
    field_name = str(params.get("field") or params.get("by") or "")
    if field_name:
        keys.append((field_name, str(params.get("order") or "asc").lower() == "desc"))
    if not keys:
        return None
    output = list(records)
    for key_name, reverse in reversed(keys):
        present = [record for record in output if _value(record, key_name) not in (None, "")]
        missing = [record for record in output if _value(record, key_name) in (None, "")]
        numeric = bool(present) and all(_number(_value(record, key_name)) is not None for record in present)
        if numeric:
            present.sort(key=lambda record: _number(_value(record, key_name)) or Decimal("0"), reverse=reverse)
        else:
            present.sort(key=lambda record: str(_value(record, key_name) or ""), reverse=reverse)
        output = [*present, *missing]
    return output


def _deduplicate(records: list[StructuredRecord], params: dict[str, object]) -> list[StructuredRecord] | None:
    fields = _field_list(params.get("fields") or params.get("keys"))
    if not fields:
        return None
    keep = str(params.get("keep") or "first").lower()
    iterable = reversed(records) if keep == "last" else records
    seen: set[tuple[str, ...]] = set()
    selected: list[StructuredRecord] = []
    for record in iterable:
        key = tuple(str(_value(record, field) or "").strip().lower() for field in fields)
        if key in seen:
            continue
        seen.add(key)
        selected.append(record)
    if keep == "last":
        selected.reverse()
    return selected


def _rank(records: list[StructuredRecord], params: dict[str, object]) -> bool:
    field_name = str(params.get("field") or params.get("by") or "")
    output_field = str(params.get("output_field") or "排名")
    group_fields = _field_list(params.get("group_by"))
    if not field_name:
        return False
    groups: dict[tuple[str, ...], list[StructuredRecord]] = {}
    for record in records:
        key = tuple(str(_value(record, field) or "") for field in group_fields) if group_fields else ("__all__",)
        groups.setdefault(key, []).append(record)
    reverse = str(params.get("order") or "desc").lower() == "desc"
    method = str(params.get("method") or "dense").lower()

    def comparable(record: StructuredRecord) -> Decimal:
        return _number(_value(record, field_name)) or Decimal("0")

    for members in groups.values():
        ordered = sorted(members, key=comparable, reverse=reverse)
        last_value: Decimal | None = None
        dense_rank = 0
        for position, record in enumerate(ordered, start=1):
            value = comparable(record)
            if last_value is None or value != last_value:
                dense_rank += 1
                last_value = value
            record.values[output_field] = dense_rank if method == "dense" else position
            if record.field_sources.get(field_name):
                record.field_sources[output_field] = list(record.field_sources[field_name])
    return True


def _pivot(records: list[StructuredRecord], params: dict[str, object]) -> list[StructuredRecord] | None:
    index_fields = _field_list(params.get("index") or params.get("index_fields"))
    column_field = str(params.get("columns") or "")
    value_field = str(params.get("values") or params.get("value_field") or "")
    if not column_field or not value_field:
        return None
    groups: dict[tuple[object, ...], list[StructuredRecord]] = {}
    for record in records:
        key = tuple(_value(record, field) for field in index_fields) if index_fields else ("__all__",)
        groups.setdefault(key, []).append(record)
    output: list[StructuredRecord] = []
    for index, (key, members) in enumerate(groups.items()):
        values = {field: key[position] for position, field in enumerate(index_fields)}
        sources: dict[str, list[str]] = {}
        for member in members:
            dynamic_field = str(_value(member, column_field) or "").strip()
            if not dynamic_field:
                continue
            value = _value(member, value_field)
            if dynamic_field in values and values[dynamic_field] not in (None, value):
                return None
            values[dynamic_field] = value
            sources[dynamic_field] = list(member.field_sources.get(value_field, []))
        output.append(
            StructuredRecord(
                record_id=f"pivot-{index}",
                target_table_id=members[0].target_table_id,
                values=values,
                field_sources=sources,
                confidence=min((member.confidence for member in members), default=0.0),
                notes=["Pivoted deterministic records."],
            )
        )
    return output


def _unpivot(records: list[StructuredRecord], params: dict[str, object]) -> list[StructuredRecord] | None:
    id_fields = _field_list(params.get("id_fields") or params.get("index"))
    value_fields = _field_list(params.get("value_fields") or params.get("fields"))
    variable_field = str(params.get("variable_field") or "字段")
    value_field = str(params.get("value_field") or "值")
    if not value_fields:
        return None
    output: list[StructuredRecord] = []
    for record in records:
        for source_field in value_fields:
            values = {field: _value(record, field) for field in id_fields}
            values[variable_field] = source_field
            values[value_field] = _value(record, source_field)
            output.append(
                StructuredRecord(
                    record_id=f"unpivot:{record.record_id}:{source_field}",
                    target_table_id=record.target_table_id,
                    values=values,
                    field_sources={value_field: list(record.field_sources.get(source_field, []))},
                    confidence=record.confidence,
                    notes=[*record.notes, "Unpivoted deterministic record."],
                )
            )
    return output


def _window(records: list[StructuredRecord], params: dict[str, object]) -> bool:
    field_name = str(params.get("field") or "")
    output_field = str(params.get("output_field") or "")
    function = str(params.get("function") or "").lower()
    group_fields = _field_list(params.get("group_by"))
    order_field = str(params.get("order_by") or "")
    if not field_name or not output_field:
        return False
    groups: dict[tuple[str, ...], list[StructuredRecord]] = {}
    for record in records:
        key = tuple(str(_value(record, field) or "") for field in group_fields) if group_fields else ("__all__",)
        groups.setdefault(key, []).append(record)
    for members in groups.values():
        if order_field:
            members.sort(key=lambda record: str(_value(record, order_field) or ""))
        running: list[Decimal] = []
        try:
            window_size = max(int(str(params.get("window_size") or 3)), 1)
        except (TypeError, ValueError):
            return False
        for record in members:
            number = _number(_value(record, field_name))
            if number is None:
                continue
            running.append(number)
            if function in {"cumulative_sum", "cumsum"}:
                result = sum(running, Decimal("0"))
            elif function in {"rolling_average", "moving_average"}:
                active = running[-window_size:]
                result = sum(active, Decimal("0")) / Decimal(len(active))
            else:
                return False
            record.values[output_field] = int(result) if result == result.to_integral_value() else float(result)
            record.field_sources[output_field] = list(record.field_sources.get(field_name, []))
    return True


def _derive(records: list[StructuredRecord], params: dict[str, object]) -> bool:
    output_field = str(params.get("output_field") or params.get("field") or "")
    operator = str(params.get("operator") or "").lower()
    fields = _field_list(params.get("fields"))
    if not fields:
        fields = _field_list(params.get("left") or params.get("numerator")) + _field_list(
            params.get("right") or params.get("denominator")
        )
    if not output_field or len(fields) < 2:
        return False
    changed = False
    for record in records:
        left = _number(_value(record, fields[0]))
        right = _number(_value(record, fields[1]))
        if left is None or right is None:
            continue
        if operator in {"add", "sum", "+"}:
            value = left + right
        elif operator in {"subtract", "difference", "-"}:
            value = left - right
        elif operator in {"multiply", "product", "*"}:
            value = left * right
        elif operator in {"divide", "ratio", "/"}:
            if right == 0:
                continue
            value = left / right
        elif operator in {"growth_rate", "growth", "change_rate"}:
            if left == 0:
                continue
            value = (right - left) / left
            if params.get("percentage"):
                value *= Decimal("100")
        else:
            return False
        record.values[output_field] = int(value) if value == value.to_integral_value() else float(value)
        evidence_ids = [
            *record.field_sources.get(fields[0], []),
            *record.field_sources.get(fields[1], []),
        ]
        if evidence_ids:
            record.field_sources[output_field] = list(dict.fromkeys(evidence_ids))
        record.notes.append(f"Derived '{output_field}' using {operator} over {fields[:2]}.")
        changed = True
    return changed


class TaskPlanExecutor:
    """Execute supported operations while preserving compatibility with agent-produced records."""

    def execute(
        self,
        records: list[StructuredRecord],
        plan: TaskPlan | None,
        *,
        source_datasets: dict[str, list[StructuredRecord]] | None = None,
        target_fields: list[str] | None = None,
    ) -> ExecutionResult:
        result = ExecutionResult(records=list(records))
        if plan is None:
            return result
        if plan.validation_errors:
            result.warnings.extend(plan.validation_errors)
            result.skipped_operations.extend(operation.operation_id for operation in plan.operations)
            return result
        datasets = {key: list(value) for key, value in (source_datasets or {}).items()}
        datasets["records"] = result.records
        datasets.setdefault("source", result.records)
        current = result.records
        group_fields: list[str] = []
        for operation in plan.operations:
            op = operation.op
            operation_input = next((datasets[name] for name in operation.inputs if name in datasets and datasets[name]), current)
            current = list(operation_input)
            before_count = len(current)
            if op in {"filter", "exclude"}:
                if not _conditions(operation.params):
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: no valid conditions were provided.")
                    continue
                current = _filter(current, operation.params, exclude=op == "exclude")
            elif op == "sort":
                sorted_records = _sort_records(current, operation.params)
                if sorted_records is None:
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: no sortable field was provided.")
                    continue
                current = sorted_records
            elif op == "limit":
                try:
                    count = int(str(operation.params.get("n") or operation.params.get("limit") or 0))
                except (TypeError, ValueError):
                    count = 0
                if count > 0:
                    current = current[:count]
            elif op == "group_by":
                raw_fields = operation.params.get("fields") or operation.params.get("by") or []
                group_fields = [str(value) for value in raw_fields] if isinstance(raw_fields, list) else [str(raw_fields)]
            elif op == "impute":
                if not _impute(current, operation.params):
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: source field is unavailable.")
                    continue
            elif op == "normalize_unit":
                if not _normalize_unit(current, operation.params):
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: unit conversion is unavailable.")
                    continue
            elif op == "aggregate":
                operation_groups = operation.params.get("group_by") or operation.params.get("group_fields") or group_fields
                aggregate_groups = _field_list(operation_groups)
                aggregated = _aggregate(current, operation.params, aggregate_groups)
                if aggregated is None:
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: aggregate inputs are unavailable.")
                    continue
                current = aggregated
            elif op == "join":
                join_inputs = [datasets[name] for name in operation.inputs if name in datasets]
                if len(join_inputs) < 2:
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: join datasets are unavailable.")
                    continue
                joined, join_warnings = _join_records(join_inputs[0], join_inputs[1], operation.params)
                result.warnings.extend(f"{operation.operation_id}: {warning}" for warning in join_warnings)
                if joined is None:
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: join keys are invalid.")
                    continue
                current = joined
            elif op == "derive":
                if not _derive(current, operation.params):
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: derive inputs or operator are invalid.")
                    continue
            elif op == "project":
                fields = operation.params.get("fields") or []
                if isinstance(fields, list) and fields:
                    for record in current:
                        record.values = {str(field): _value(record, str(field)) for field in fields}
            elif op == "deduplicate":
                deduplicated = _deduplicate(current, operation.params)
                if deduplicated is None:
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: deduplication keys are unavailable.")
                    continue
                current = deduplicated
            elif op == "rank":
                if not _rank(current, operation.params):
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: rank field is unavailable.")
                    continue
            elif op == "pivot":
                pivoted = _pivot(current, operation.params)
                if pivoted is None:
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: pivot inputs are invalid or conflicting.")
                    continue
                current = pivoted
            elif op == "unpivot":
                unpivoted = _unpivot(current, operation.params)
                if unpivoted is None:
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: unpivot fields are unavailable.")
                    continue
                current = unpivoted
            elif op == "window":
                if not _window(current, operation.params):
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: window parameters are invalid.")
                    continue
            else:
                result.skipped_operations.append(operation.operation_id)
                result.warnings.append(f"Skipped unsupported operation {operation.operation_id} ({op}).")
                continue
            result.applied_operations.append(operation.operation_id)
            result.operation_metrics.append(
                {
                    "operation_id": operation.operation_id,
                    "op": operation.op,
                    "input_count": before_count,
                    "output_count": len(current),
                }
            )
            if operation.output:
                datasets[operation.output] = current
        if target_fields and current is not result.records:
            for record in current:
                record.values = {field_name: _value(record, field_name) for field_name in target_fields}
            current = [record for record in current if any(value not in (None, "") for value in record.values.values())]
        result.records = current
        return result
