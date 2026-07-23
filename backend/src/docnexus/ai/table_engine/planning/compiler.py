"""Compile LLM task-understanding output into an executable TaskPlan."""

from __future__ import annotations

from docnexus.ai.table_engine.core.models import Constraint, TaskOperation, TaskPlan, TaskSpec
from docnexus.ai.table_engine.planning.validator import validate_task_plan

ALLOWED_OPERATIONS = {
    "deduplicate",
    "filter",
    "exclude",
    "group_by",
    "aggregate",
    "sort",
    "limit",
    "normalize_unit",
    "impute",
    "join",
    "derive",
    "project",
    "pivot",
    "rank",
    "unpivot",
    "window",
}
COMPARISON_OPERATORS = {">", ">=", "<", "<=", "=", "==", "eq", "gt", "gte", "lt", "lte"}


def _normalize(value: object) -> str:
    return "".join(str(value or "").lower().split()).replace("_", "").replace("-", "")


def _resolve_field(value: object, target_fields: list[str]) -> str | None:
    normalized = _normalize(value)
    if not normalized:
        return None
    exact = next((field for field in target_fields if _normalize(field) == normalized), None)
    if exact:
        return exact
    matches = [field for field in target_fields if normalized in _normalize(field) or _normalize(field) in normalized]
    return max(matches, key=len) if matches else None


def _operation_from_dict(raw: dict[str, object], index: int, target_fields: list[str]) -> TaskOperation | None:
    op = str(raw.get("op") or "").strip().lower()
    if op not in ALLOWED_OPERATIONS:
        return None
    raw_params = raw.get("params")
    params: dict[str, object] = dict(raw_params) if isinstance(raw_params, dict) else {}
    if "group_fields" in params and "group_by" not in params:
        params["group_by"] = params["group_fields"]
    for key in ("field", "by", "group_by"):
        value = params.get(key)
        if isinstance(value, str):
            params[key] = _resolve_field(value, target_fields) or value
        elif isinstance(value, list):
            params[key] = [_resolve_field(item, target_fields) or item for item in value]
    conditions = params.get("conditions")
    if isinstance(conditions, list):
        normalized_conditions = []
        for condition in conditions:
            if not isinstance(condition, dict):
                continue
            normalized_condition = dict(condition)
            if condition.get("field"):
                normalized_condition["field"] = _resolve_field(condition["field"], target_fields) or condition["field"]
            normalized_conditions.append(normalized_condition)
        params["conditions"] = normalized_conditions
    raw_metrics = params.get("metrics") or params.get("aggregations")
    if isinstance(raw_metrics, list):
        normalized_metrics = []
        for metric in raw_metrics:
            if not isinstance(metric, dict):
                continue
            normalized_metric = dict(metric)
            if metric.get("output_field") and not metric.get("alias"):
                normalized_metric["alias"] = metric["output_field"]
            normalized_metrics.append(normalized_metric)
        if "metrics" in params:
            params["metrics"] = normalized_metrics
        else:
            params["aggregations"] = normalized_metrics
    raw_inputs = raw.get("inputs")
    raw_dependencies = raw.get("depends_on")
    return TaskOperation(
        operation_id=str(raw.get("operation_id") or raw.get("id") or f"op-{index}"),
        op=op,
        target_table_id=str(raw["target_table_id"]) if raw.get("target_table_id") else None,
        inputs=[str(value) for value in raw_inputs] if isinstance(raw_inputs, list) else [],
        output=str(raw["output"]) if raw.get("output") else None,
        params=params,
        depends_on=[str(value) for value in raw_dependencies] if isinstance(raw_dependencies, list) else [],
    )


def _compile_constraints(
    raw_constraints: object,
    *,
    task_id: str,
    target_fields: list[str],
) -> tuple[list[Constraint], list[TaskOperation]]:
    constraints: list[Constraint] = []
    operations: list[TaskOperation] = []
    if not isinstance(raw_constraints, list):
        return constraints, operations
    for index, raw in enumerate(raw_constraints):
        if not isinstance(raw, dict):
            continue
        field_name = _resolve_field(raw.get("field"), target_fields)
        operator = str(raw.get("operator") or "=").lower()
        value = raw.get("value")
        raw_kind = str(raw.get("kind") or "")
        if operator == "group_by":
            operations.append(
                TaskOperation(
                    operation_id=f"llm-group-{index}",
                    op="group_by",
                    params={"fields": [field_name or str(raw.get("field") or value)]},
                )
            )
            continue
        if field_name and operator in COMPARISON_OPERATORS:
            kind = "field_filter" if operator not in {"=", "==", "eq"} else ("entity" if raw_kind == "entity" else "field_filter")
            constraints.append(
                Constraint(
                    constraint_id=f"{task_id}#llm-{index}",
                    source="llm_task_plan",
                    kind=kind,
                    field=field_name,
                    operator=operator,
                    value=value,
                )
            )
            operations.append(
                TaskOperation(
                    operation_id=f"llm-filter-{index}",
                    op="filter",
                    params={"conditions": [{"field": field_name, "operator": operator, "value": value}]},
                )
            )
    return constraints, operations


def _constraint_key(constraint: Constraint) -> tuple[str, str | None, str, str]:
    return constraint.kind, constraint.field, constraint.operator, str(constraint.value)


def compile_task_understanding(task_spec: TaskSpec, result: dict[str, object] | None) -> TaskPlan:
    """Compile an LLM result, merge safe constraints, and attach the plan to TaskSpec."""
    if not result:
        plan = TaskPlan(source="deterministic")
        task_spec.task_plan = plan
        return plan

    operations: list[TaskOperation] = []
    raw_operations = result.get("operations")
    if isinstance(raw_operations, list):
        for index, raw_operation in enumerate(raw_operations):
            if isinstance(raw_operation, dict):
                operation = _operation_from_dict(raw_operation, index, task_spec.target_fields)
                if operation:
                    operations.append(operation)

    llm_constraints, constraint_operations = _compile_constraints(
        result.get("constraints"),
        task_id=task_spec.task_id,
        target_fields=task_spec.target_fields,
    )
    if not operations:
        operations = constraint_operations

    aggregate_metrics: list[dict[str, object]] = []
    for operation in operations:
        if operation.op == "aggregate":
            raw_metrics = operation.params.get("metrics") or operation.params.get("aggregations") or []
            if isinstance(raw_metrics, list):
                aggregate_metrics.extend(metric for metric in raw_metrics if isinstance(metric, dict))
    for operation in operations:
        if operation.op != "impute":
            continue
        impute_field = str(operation.params.get("field") or "")
        for metric in aggregate_metrics:
            output_field = str(metric.get("alias") or metric.get("output_field") or "")
            source_field = str(metric.get("field") or "")
            if impute_field and source_field and _normalize(impute_field) == _normalize(output_field):
                operation.params["field"] = source_field
                break

    seen = {_constraint_key(constraint) for constraint in task_spec.constraints}
    for constraint in llm_constraints:
        key = _constraint_key(constraint)
        if key not in seen:
            task_spec.constraints.append(constraint)
            seen.add(key)

    unresolved = result.get("unresolved") or []
    plan = TaskPlan(
        operations=operations,
        unresolved=[str(value) for value in unresolved] if isinstance(unresolved, list) else [],
        source="llm",
    )
    validation = validate_task_plan(plan)
    if len(task_spec.target_tables) > 1:
        target_table_ids = set(task_spec.target_tables)
        for operation in plan.operations:
            if not operation.target_table_id:
                validation.errors.append(
                    f"{operation.operation_id}: target_table_id is required for a multi-table task."
                )
            elif operation.target_table_id not in target_table_ids:
                validation.errors.append(
                    f"{operation.operation_id}: unknown target_table_id '{operation.target_table_id}'."
                )
        validation.valid = not validation.errors
    plan.validation_errors = validation.errors
    plan.validation_warnings = validation.warnings
    plan.unresolved.extend(error for error in validation.errors if error not in plan.unresolved)
    task_spec.task_plan = plan
    return plan
