from __future__ import annotations

import docnexus.ai.table_engine.agents as agents_module
from docnexus.ai.table_engine.agents import RepairAgent, _finalize_candidates_by_task
from docnexus.ai.table_engine.candidates.models import CandidateRecord
from docnexus.ai.table_engine.core.models import (
    CanonicalDocument,
    Constraint,
    DocumentBlock,
    EvidenceItem,
    EvidencePack,
    FieldSpec,
    FileAsset,
    FillResult,
    LocationRef,
    StructuredRecord,
    TargetTableSpec,
    TaskOperation,
    TaskPlan,
    TaskSpec,
    TemplateSpec,
    VerificationCheck,
    VerificationReport,
)
from docnexus.ai.table_engine.core.runtime import AgentState
from docnexus.ai.table_engine.execution import TaskPlanExecutor, build_source_datasets
from docnexus.ai.table_engine.planners import DefaultTaskPlanner
from docnexus.ai.table_engine.planning import compile_task_understanding, validate_task_plan
from docnexus.ai.table_engine.verifiers import DefaultVerifier, _task_constraint_violations


def _request_doc(text: str) -> CanonicalDocument:
    return CanonicalDocument(
        doc_id="request",
        file=FileAsset("request", "/tmp/request.txt", "request.txt", "txt", "user_request", None, 1),
        doc_type="txt",
        blocks=[DocumentBlock("request#block-0", "paragraph", text, LocationRef("request", paragraph_index=0))],
    )


def _sales_template() -> TemplateSpec:
    names = ["门店", "区域", "销售额", "利润率"]
    return TemplateSpec(
        template_doc_id="template",
        target_tables=[
            TargetTableSpec(
                target_table_id="sales",
                logical_name="销售",
                schema=[
                    FieldSpec(str(index), name, name, "number" if name in {"销售额", "利润率"} else "string", False)
                    for index, name in enumerate(names)
                ],
            )
        ],
    )


def test_planner_parses_multiple_comparisons_and_chinese_top_n() -> None:
    task = DefaultTaskPlanner().plan(
        _request_doc("华东区域销售额不低于100且利润率超过20，按利润率从高到低取前三名。"),
        _sales_template(),
        [],
    )

    filters = {(constraint.field, constraint.operator, constraint.value) for constraint in task.constraints if constraint.kind == "field_filter"}
    assert ("销售额", ">=", 100) in filters
    assert ("利润率", ">", 20) in filters
    assert not any(constraint.field == "区域" and constraint.kind == "field_filter" for constraint in task.constraints)
    assert any(constraint.kind == "limit" and constraint.value == 3 for constraint in task.constraints)


def test_all_candidates_that_violate_constraints_are_removed() -> None:
    task = TaskSpec(
        "task",
        "fill_table",
        "template",
        constraints=[Constraint("filter", "user_request", "field_filter", "销售额", ">", 100)],
    )
    candidate = CandidateRecord("r1", "sales", {"门店": "A"}, {"门店": "A", "销售额": 50}, confidence=0.9)

    assert _finalize_candidates_by_task([candidate], task) == []


def test_legacy_llm_constraints_compile_to_executable_types() -> None:
    task = TaskSpec("task", "fill_table", "template", target_fields=["门店", "区域", "销售额", "利润率"])
    result = {
        "constraints": [
            {"kind": "entity", "field": "销售额", "operator": ">=", "value": 100},
            {"kind": "entity", "field": "区域", "operator": "group_by", "value": "区域"},
        ]
    }

    plan = compile_task_understanding(task, result)

    assert any(constraint.kind == "field_filter" and constraint.field == "销售额" for constraint in task.constraints)
    assert [operation.op for operation in plan.operations] == ["filter", "group_by"]


def test_compiler_normalizes_aggregate_aliases_and_impute_source_field() -> None:
    task = TaskSpec("task", "fill_table", "template", target_fields=["区域", "平均销售额"])
    result = {
        "operations": [
            {"operation_id": "impute", "op": "impute", "params": {"field": "平均销售额", "group_fields": ["区域"]}},
            {
                "operation_id": "aggregate",
                "op": "aggregate",
                "params": {
                    "aggregations": [
                        {"field": "销售额", "function": "mean", "output_field": "平均销售额"},
                    ]
                },
            },
        ]
    }

    plan = compile_task_understanding(task, result)

    assert plan.operations[0].params["field"] == "销售额"
    assert plan.operations[0].params["group_by"] == ["区域"]
    assert plan.operations[1].params["aggregations"][0]["alias"] == "平均销售额"


def test_validator_rejects_duplicate_ids_unknown_dependencies_and_cycles() -> None:
    plan = TaskPlan(
        operations=[
            TaskOperation("same", "limit", params={"n": 1}, depends_on=["missing"]),
            TaskOperation("same", "project", params={"fields": ["区域"]}, depends_on=["same"]),
        ]
    )

    validation = validate_task_plan(plan)

    assert not validation.valid
    assert any("Duplicate operation ids" in error for error in validation.errors)
    assert any("unknown dependencies" in error for error in validation.errors)
    assert any("cannot depend on itself" in error for error in validation.errors)


def test_validator_rejects_forward_dependencies_and_reserved_outputs() -> None:
    plan = TaskPlan(
        operations=[
            TaskOperation("first", "limit", output="source", params={"n": 1}, depends_on=["later"]),
            TaskOperation("later", "project", output="result", params={"fields": ["地区"]}),
        ]
    )

    validation = validate_task_plan(plan)

    assert not validation.valid
    assert any("dependencies must appear earlier" in error for error in validation.errors)
    assert any("is reserved" in error for error in validation.errors)


def test_executor_does_not_run_invalid_plan() -> None:
    record = StructuredRecord("r1", "sales", {"销售额": 50})
    plan = TaskPlan(
        operations=[TaskOperation("filter", "filter", params={})],
        validation_errors=["filter: filter requires non-empty conditions."],
    )

    result = TaskPlanExecutor().execute([record], plan)

    assert result.records == [record]
    assert result.skipped_operations == ["filter"]


def test_executor_imputes_before_group_aggregate_and_post_filters() -> None:
    records = [
        StructuredRecord("e1", "sales", {"区域": "华东", "销售额": 100}, confidence=0.9),
        StructuredRecord("e2", "sales", {"区域": "华东", "销售额": None}, confidence=0.9),
        StructuredRecord("e3", "sales", {"区域": "华东", "销售额": 300}, confidence=0.9),
        StructuredRecord("n1", "sales", {"区域": "华北", "销售额": 50}, confidence=0.9),
        StructuredRecord("n2", "sales", {"区域": "华北", "销售额": None}, confidence=0.9),
        StructuredRecord("n3", "sales", {"区域": "华北", "销售额": 70}, confidence=0.9),
    ]
    plan = TaskPlan(
        operations=[
            TaskOperation("impute", "impute", params={"field": "销售额", "method": "median", "group_by": ["区域"]}),
            TaskOperation("group", "group_by", params={"fields": ["区域"]}),
            TaskOperation(
                "average",
                "aggregate",
                params={"aggregations": [{"field": "销售额", "function": "mean", "alias": "平均销售额"}]},
            ),
            TaskOperation(
                "keep",
                "filter",
                params={"stage": "post_aggregate", "conditions": [{"field": "平均销售额", "operator": ">", "value": 100}]},
            ),
        ]
    )

    result = TaskPlanExecutor().execute(records, plan)

    assert [record.values for record in result.records] == [{"区域": "华东", "平均销售额": 200}]
    assert result.skipped_operations == []


def test_source_datasets_can_be_joined_and_derived() -> None:
    left_doc = CanonicalDocument(
        doc_id="orders",
        file=FileAsset("orders", "/tmp/orders.xlsx", "orders.xlsx", "xlsx", "source", None, 1),
        doc_type="xlsx",
    )
    right_doc = CanonicalDocument(
        doc_id="costs",
        file=FileAsset("costs", "/tmp/costs.xlsx", "costs.xlsx", "xlsx", "source", None, 1),
        doc_type="xlsx",
    )
    evidence = EvidencePack(
        "task",
        [
            EvidenceItem("order-1", "row", "orders", {"商品": "A", "销售额": 120}),
            EvidenceItem("cost-1", "row", "costs", {"商品": "A", "成本": 80}),
        ],
    )
    datasets = build_source_datasets(evidence, [left_doc, right_doc], target_table_id="profit")
    plan = TaskPlan(
        operations=[
            TaskOperation(
                "join",
                "join",
                inputs=["orders", "costs"],
                output="joined",
                params={"on": "商品"},
            ),
            TaskOperation(
                "profit",
                "derive",
                inputs=["joined"],
                params={"output_field": "利润", "operator": "subtract", "fields": ["销售额", "成本"]},
            ),
        ]
    )

    result = TaskPlanExecutor().execute(
        [],
        plan,
        source_datasets=datasets,
        target_fields=["商品", "销售额", "成本", "利润"],
    )

    assert [record.values for record in result.records] == [{"商品": "A", "销售额": 120, "成本": 80, "利润": 40}]
    assert result.applied_operations == ["join", "profit"]
    assert result.records[0].field_sources["利润"] == ["order-1", "cost-1"]


def test_repair_agent_retries_once_with_a_valid_replacement_plan(monkeypatch) -> None:
    task = TaskSpec("task", "fill_table", "template", target_fields=["地区"])
    task.task_plan = TaskPlan(
        operations=[TaskOperation("broken", "filter", params={})],
        validation_errors=["broken plan"],
    )
    failed_report = VerificationReport(
        "task",
        "fail",
        "failed",
        checks=[VerificationCheck("task_plan_validation", "fail", "invalid", ["broken plan"])],
    )
    state = AgentState(
        task_spec=task,
        template_spec=_sales_template(),
        user_request_doc=_request_doc("按地区输出"),
        verification_report=failed_report,
    )
    monkeypatch.setattr(
        agents_module,
        "_run_skill",
        lambda *args, **kwargs: {
            "intent": "fill_table",
            "constraints": [],
            "operations": [
                {
                    "operation_id": "project",
                    "op": "project",
                    "inputs": ["records"],
                    "output": "result",
                    "params": {"fields": ["地区"]},
                    "depends_on": [],
                }
            ],
            "unresolved": [],
        },
    )

    class FakeCoder:
        def run(self, current_state):
            current_state.records = [StructuredRecord("r1", "sales", {"地区": "华东"})]
            return current_state

    class FakeVerifier:
        def run(self, current_state):
            current_state.verification_report = VerificationReport("task", "pass", "repaired")
            return current_state

    repaired = RepairAgent(object(), FakeCoder(), FakeVerifier()).run(state)

    assert repaired.retry_count == 1
    assert repaired.verification_report.status == "pass"
    assert repaired.task_spec.task_plan.validation_errors == []
    assert [operation.op for operation in repaired.task_spec.task_plan.operations] == ["project"]


def test_verifier_fails_when_output_violates_filter() -> None:
    template = _sales_template()
    task = TaskSpec(
        "task",
        "fill_table",
        "template",
        constraints=[Constraint("filter", "user_request", "field_filter", "销售额", ">", 100)],
    )
    record = StructuredRecord(
        "r1",
        "sales",
        {"门店": "A", "区域": "华东", "销售额": 50, "利润率": 10},
        field_sources={"门店": ["e1"], "区域": ["e1"], "销售额": ["e1"], "利润率": ["e1"]},
        confidence=0.9,
    )

    report = DefaultVerifier().verify(
        task,
        template,
        EvidencePack("task", [EvidenceItem("e1", "row", "doc", record.values)]),
        [record],
        FillResult("output", "out.xlsx"),
    )

    assert report.status == "fail"
    check = next(check for check in report.checks if check.name == "task_constraint_compliance")
    assert check.status == "fail"


def test_verifier_accepts_entity_grouped_date_sort() -> None:
    task = TaskSpec(
        "task",
        "fill_table",
        "template",
        constraints=[Constraint("sort", "user_request", "sort", "日期", "asc", "日期")],
    )
    records = [
        StructuredRecord("a1", "t", {"国家/地区": "Albania", "日期": "2020-02-25"}),
        StructuredRecord("a2", "t", {"国家/地区": "Albania", "日期": "2020-02-27"}),
        StructuredRecord("b1", "t", {"国家/地区": "Algeria", "日期": "2020-02-25"}),
        StructuredRecord("b2", "t", {"国家/地区": "Algeria", "日期": "2020-02-26"}),
    ]

    assert _task_constraint_violations(records, task) == []
