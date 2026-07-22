"""Strict structural and dependency validation for TaskPlan v2."""

from __future__ import annotations

from dataclasses import dataclass, field

from docnexus.ai.table_engine.core.models import TaskOperation, TaskPlan

SUPPORTED_DERIVE_OPERATORS = {
    "+",
    "-",
    "*",
    "/",
    "add",
    "change_rate",
    "difference",
    "divide",
    "growth",
    "growth_rate",
    "multiply",
    "product",
    "ratio",
    "subtract",
    "sum",
}


@dataclass(slots=True)
class TaskPlanValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _has_sequence(params: dict[str, object], *keys: str) -> bool:
    return any(isinstance(params.get(key), list) and bool(params.get(key)) for key in keys)


def _operation_parameter_errors(operation: TaskOperation) -> list[str]:
    params = operation.params
    prefix = operation.operation_id
    if operation.op in {"filter", "exclude"} and not _has_sequence(params, "conditions"):
        return [f"{prefix}: {operation.op} requires non-empty conditions."]
    if operation.op == "sort" and not (params.get("field") or params.get("by") or _has_sequence(params, "keys")):
        return [f"{prefix}: sort requires field, by, or keys."]
    if operation.op == "limit" and not (params.get("n") or params.get("limit")):
        return [f"{prefix}: limit requires a positive n or limit."]
    if operation.op == "group_by" and not (params.get("fields") or params.get("by") or params.get("group_by")):
        return [f"{prefix}: group_by requires fields."]
    if operation.op == "aggregate" and not _has_sequence(params, "metrics", "aggregations"):
        return [f"{prefix}: aggregate requires metrics or aggregations."]
    if operation.op == "impute" and not params.get("field"):
        return [f"{prefix}: impute requires field."]
    if operation.op == "join":
        if len(operation.inputs) < 2:
            return [f"{prefix}: join requires two input datasets."]
        if not (params.get("on") or params.get("left_on") or params.get("right_on") or _has_sequence(params, "keys")):
            return [f"{prefix}: join requires on, left_on/right_on, or keys."]
        if bool(params.get("left_on")) != bool(params.get("right_on")):
            return [f"{prefix}: join requires both left_on and right_on."]
    if operation.op == "derive" and not (params.get("output_field") or params.get("field")):
        return [f"{prefix}: derive requires output_field."]
    if operation.op == "derive":
        operator = str(params.get("operator") or "").lower()
        if operator not in SUPPORTED_DERIVE_OPERATORS:
            return [f"{prefix}: derive requires a supported operator."]
        fields = params.get("fields")
        has_pair = isinstance(fields, list) and len(fields) >= 2
        has_left_right = bool(params.get("left") or params.get("numerator")) and bool(
            params.get("right") or params.get("denominator")
        )
        if not has_pair and not has_left_right:
            return [f"{prefix}: derive requires two input fields."]
    if operation.op == "project" and not _has_sequence(params, "fields"):
        return [f"{prefix}: project requires fields."]
    return []


def _cycle_errors(operations: list[TaskOperation]) -> list[str]:
    graph = {operation.operation_id: list(operation.depends_on) for operation in operations}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, trail: list[str]) -> list[str]:
        if node in visiting:
            cycle_start = trail.index(node) if node in trail else 0
            return [f"Dependency cycle detected: {' -> '.join([*trail[cycle_start:], node])}."]
        if node in visited:
            return []
        visiting.add(node)
        for dependency in graph.get(node, []):
            errors = visit(dependency, [*trail, node])
            if errors:
                return errors
        visiting.remove(node)
        visited.add(node)
        return []

    for operation_id in graph:
        errors = visit(operation_id, [])
        if errors:
            return errors
    return []


def validate_task_plan(plan: TaskPlan) -> TaskPlanValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    operation_ids = [operation.operation_id for operation in plan.operations]
    duplicate_ids = sorted({operation_id for operation_id in operation_ids if operation_ids.count(operation_id) > 1})
    if duplicate_ids:
        errors.append(f"Duplicate operation ids: {', '.join(duplicate_ids)}.")

    known_ids = set(operation_ids)
    operation_positions = {operation_id: index for index, operation_id in enumerate(operation_ids)}
    produced_outputs: set[str] = set()
    for index, operation in enumerate(plan.operations):
        errors.extend(_operation_parameter_errors(operation))
        unknown_dependencies = [dependency for dependency in operation.depends_on if dependency not in known_ids]
        if unknown_dependencies:
            errors.append(
                f"{operation.operation_id}: unknown dependencies: {', '.join(unknown_dependencies)}."
            )
        if operation.operation_id in operation.depends_on:
            errors.append(f"{operation.operation_id}: operation cannot depend on itself.")
        forward_dependencies = [
            dependency
            for dependency in operation.depends_on
            if dependency in operation_positions and operation_positions[dependency] >= index
        ]
        if forward_dependencies:
            errors.append(
                f"{operation.operation_id}: dependencies must appear earlier: {', '.join(forward_dependencies)}."
            )
        if operation.output:
            if operation.output in {"source", "records"}:
                errors.append(f"{operation.operation_id}: output dataset name '{operation.output}' is reserved.")
            if operation.output in produced_outputs:
                errors.append(f"Duplicate output dataset: {operation.output}.")
            produced_outputs.add(operation.output)
        if not operation.depends_on and operation.inputs and all(value not in {"source", "records"} for value in operation.inputs):
            warnings.append(f"{operation.operation_id}: root operation references external dataset(s).")

    errors.extend(_cycle_errors(plan.operations))
    return TaskPlanValidationResult(valid=not errors, errors=list(dict.fromkeys(errors)), warnings=list(dict.fromkeys(warnings)))
