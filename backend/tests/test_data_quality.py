from docnexus.ai.table_engine.core.models import (
    Constraint,
    EvidenceItem,
    EvidencePack,
    FieldSpec,
    StructuredRecord,
    TargetTableSpec,
    TaskOperation,
    TaskPlan,
    TaskSpec,
    TemplateSpec,
)
from docnexus.ai.table_engine.quality import build_data_quality_checks


def _template() -> TemplateSpec:
    return TemplateSpec(
        "template",
        [
            TargetTableSpec(
                "sales",
                "销售",
                [
                    FieldSpec("city", "城市", "城市", "string", True),
                    FieldSpec("date", "日期", "日期", "date", True),
                    FieldSpec("amount", "销售额", "销售额", "number", True),
                ],
            )
        ],
    )


def test_quality_checks_detect_duplicates_conflicts_units_and_date_gaps() -> None:
    task = TaskSpec(
        "task",
        "fill_table",
        "template",
        constraints=[Constraint("request", "user_request", "request_text", None, "contains", "输出每日数据")],
    )
    records = [
        StructuredRecord("r1", "sales", {"城市": "甲", "日期": "2026-01-01", "销售额": "1万元"}),
        StructuredRecord("r2", "sales", {"城市": "甲", "日期": "2026-01-01", "销售额": "2元"}),
        StructuredRecord("r3", "sales", {"城市": "甲", "日期": "2026-01-03", "销售额": "3万元"}),
    ]
    evidence = EvidencePack(
        "task",
        [
            EvidenceItem("e1", "row", "doc-a", {"城市": "甲", "日期": "2026-01-01", "销售额": 1}),
            EvidenceItem("e2", "row", "doc-b", {"城市": "甲", "日期": "2026-01-01", "销售额": 2}),
        ],
    )

    checks = {check.name: check for check in build_data_quality_checks(task, _template(), evidence, records)}

    assert checks["primary_key_uniqueness"].status == "fail"
    assert checks["cross_source_consistency"].status == "warning"
    assert checks["unit_consistency"].status == "warning"
    assert checks["date_continuity"].status == "warning"


def test_quality_checks_pass_for_clean_records() -> None:
    task = TaskSpec("task", "fill_table", "template")
    records = [StructuredRecord("r1", "sales", {"城市": "甲", "日期": "2026-01-01", "销售额": 1})]

    checks = build_data_quality_checks(task, _template(), EvidencePack("task"), records)

    assert all(check.status == "pass" for check in checks)


def test_aggregate_reconciliation_fails_for_incorrect_total() -> None:
    task = TaskSpec("task", "fill_table", "template")
    task.task_plan = TaskPlan(
        operations=[
            TaskOperation(
                "sum",
                "aggregate",
                target_table_id="sales",
                inputs=["source"],
                params={"group_by": ["城市"], "aggregations": [{"field": "销售额", "function": "sum", "alias": "销售额"}]},
            )
        ]
    )
    evidence = EvidencePack(
        "task",
        [
            EvidenceItem("e1", "row", "doc", {"城市": "甲", "销售额": 10}),
            EvidenceItem("e2", "row", "doc", {"城市": "甲", "销售额": 20}),
        ],
    )
    records = [StructuredRecord("r1", "sales", {"城市": "甲", "销售额": 25})]

    checks = {check.name: check for check in build_data_quality_checks(task, _template(), evidence, records)}

    assert checks["aggregate_reconciliation"].status == "fail"
