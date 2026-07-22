"""Execute validated TaskPlan operations over structured records."""

from __future__ import annotations

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
        left, right = left_number, right_number
    else:
        left, right = str(value or "").strip().lower(), str(expected or "").strip().lower()
    if normalized_operator in {">", "gt"}:
        return left > right
    if normalized_operator in {">=", "gte"}:
        return left >= right
    if normalized_operator in {"<", "lt"}:
        return left < right
    if normalized_operator in {"<=", "lte"}:
        return left <= right
    if normalized_operator in {"!=", "ne"}:
        return left != right
    if normalized_operator in {"in"} and isinstance(expected, list):
        return any(left == str(item).strip().lower() for item in expected)
    return left == right


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
    group_fields = params.get("group_by") or []
    if isinstance(group_fields, str):
        group_fields = [group_fields]
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
        replacement = Decimal(str(median(available))) if method == "median" else sum(available) / Decimal(len(available))
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
                result = sum(available) / Decimal(len(available))
            elif function == "median":
                result = Decimal(str(median(available)))
            elif function == "min":
                result = min(available)
            elif function == "max":
                result = max(available)
            elif function == "count":
                result = Decimal(len(available))
            else:
                result = sum(available)
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


def _join_records(
    left_records: list[StructuredRecord],
    right_records: list[StructuredRecord],
    params: dict[str, object],
) -> list[StructuredRecord] | None:
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
        return None

    right_index: dict[tuple[str, ...], list[StructuredRecord]] = {}
    for record in right_records:
        key = tuple(str(_value(record, field) or "").strip().lower() for field in right_fields)
        if all(key):
            right_index.setdefault(key, []).append(record)

    how = str(params.get("how") or "inner").lower()
    suffixes = params.get("suffixes") or ["_left", "_right"]
    right_suffix = str(suffixes[1]) if isinstance(suffixes, list) and len(suffixes) > 1 else "_right"
    joined: list[StructuredRecord] = []
    for left in left_records:
        key = tuple(str(_value(left, field) or "").strip().lower() for field in left_fields)
        matches = right_index.get(key, [])
        if not matches and how == "left":
            matches = [None]
        for match_index, right in enumerate(matches):
            values = dict(left.values)
            sources = {field_name: list(ids) for field_name, ids in left.field_sources.items()}
            if right is not None:
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
    return joined


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
            if op in {"filter", "exclude"}:
                if not _conditions(operation.params):
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: no valid conditions were provided.")
                    continue
                current = _filter(current, operation.params, exclude=op == "exclude")
            elif op == "sort":
                field_name = str(operation.params.get("field") or operation.params.get("by") or "")
                if not field_name:
                    result.skipped_operations.append(operation.operation_id)
                    result.warnings.append(f"Skipped {operation.operation_id}: no sortable field was provided.")
                    continue
                reverse = str(operation.params.get("order") or "asc").lower() == "desc"
                present = [record for record in current if _value(record, field_name) not in (None, "")]
                missing = [record for record in current if _value(record, field_name) in (None, "")]
                numeric = all(_number(_value(record, field_name)) is not None for record in present)
                present.sort(
                    key=(
                        (lambda record: _number(_value(record, field_name)))
                        if numeric
                        else (lambda record: str(_value(record, field_name) or ""))
                    ),
                    reverse=reverse,
                )
                current = [*present, *missing]
            elif op == "limit":
                try:
                    count = int(operation.params.get("n") or operation.params.get("limit") or 0)
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
                joined = _join_records(join_inputs[0], join_inputs[1], operation.params)
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
            else:
                result.skipped_operations.append(operation.operation_id)
                result.warnings.append(f"Skipped unsupported operation {operation.operation_id} ({op}).")
                continue
            result.applied_operations.append(operation.operation_id)
            if operation.output:
                datasets[operation.output] = current
        if target_fields and current is not result.records:
            for record in current:
                record.values = {field_name: _value(record, field_name) for field_name in target_fields}
            current = [record for record in current if any(value not in (None, "") for value in record.values.values())]
        result.records = current
        return result
