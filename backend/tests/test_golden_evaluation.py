from pathlib import Path

from docnexus.ai.table_engine.evaluation import evaluate_golden_set


def test_complex_task_golden_set_has_full_exact_match() -> None:
    fixture = Path(__file__).parent / "fixtures" / "evaluation" / "complex_tasks.json"

    summary = evaluate_golden_set(fixture)

    assert summary.case_count >= 3
    assert summary.passed_count == summary.case_count
    assert summary.exact_match_rate == 1.0
