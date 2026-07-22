"""Reproducible golden-set evaluation for deterministic task plans."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from docnexus.ai.table_engine.core.models import StructuredRecord, TaskOperation, TaskPlan
from docnexus.ai.table_engine.execution import TaskPlanExecutor


@dataclass(slots=True)
class EvaluationSummary:
    case_count: int
    passed_count: int
    exact_match_rate: float
    cases: list[dict[str, object]] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "case_count": self.case_count,
            "passed_count": self.passed_count,
            "exact_match_rate": self.exact_match_rate,
            "cases": self.cases,
        }


def _records(raw_records: list[dict[str, object]], target_table_id: str) -> list[StructuredRecord]:
    records = []
    for index, record in enumerate(raw_records):
        raw_values = record.get("values")
        values: dict[str, object] = dict(raw_values) if isinstance(raw_values, dict) else {}
        records.append(
            StructuredRecord(
                record_id=str(record.get("record_id") or f"record-{index}"),
                target_table_id=target_table_id,
                values=values,
                confidence=1.0,
            )
        )
    return records


def evaluate_golden_set(path: str | Path) -> EvaluationSummary:
    """Execute every golden case and report exact output accuracy."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = payload.get("cases", []) if isinstance(payload, dict) else []
    results: list[dict[str, object]] = []
    passed_count = 0
    for raw_case in cases:
        target_table_id = str(raw_case.get("target_table_id") or "target")
        plan = TaskPlan(
            operations=[TaskOperation(**operation) for operation in raw_case.get("operations", [])]
        )
        datasets = {
            name: _records(records, target_table_id)
            for name, records in (raw_case.get("datasets") or {}).items()
        }
        initial = _records(raw_case.get("records") or [], target_table_id)
        expected = raw_case.get("expected") or []
        execution = TaskPlanExecutor().execute(
            initial,
            plan,
            source_datasets=datasets,
            target_fields=[str(field) for field in raw_case.get("target_fields", [])] or None,
        )
        actual = [record.values for record in execution.records]
        passed = actual == expected and not execution.skipped_operations
        passed_count += int(passed)
        results.append(
            {
                "case_id": raw_case.get("case_id"),
                "passed": passed,
                "actual": actual,
                "expected": expected,
                "warnings": execution.warnings,
            }
        )
    case_count = len(results)
    return EvaluationSummary(
        case_count=case_count,
        passed_count=passed_count,
        exact_match_rate=round(passed_count / case_count, 4) if case_count else 0.0,
        cases=results,
    )
