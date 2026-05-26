import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from any2table.analyzers import DefaultTemplateAnalyzer
from any2table.core.models import (
    CanonicalDocument,
    CanonicalTable,
    FieldSpec,
    FillResult,
    LocationRef,
    TableCell,
    TableHeader,
    TableRow,
    VerificationCheck,
    VerificationReport,
)
from docnexus_ai.table_filling import _write_fill_run_report


class TemplateAnalyzerEnhancementTests(unittest.TestCase):
    def test_detects_second_row_header_and_combines_group_header(self) -> None:
        table = CanonicalTable(
            table_id="template#table-0",
            source_doc_id="template",
            table_type="xlsx_sheet_table",
            name="Sheet1",
            headers=[
                TableHeader("h0", "经济指标", "经济指标", 0),
                TableHeader("h1", "", "", 1),
                TableHeader("h2", "", "", 2),
            ],
            rows=[
                TableRow("r0", 0, [
                    TableCell(0, 0, "经济指标"),
                    TableCell(0, 1, ""),
                    TableCell(0, 2, ""),
                ]),
                TableRow("r1", 1, [
                    TableCell(1, 0, "城市"),
                    TableCell(1, 1, "GDP"),
                    TableCell(1, 2, "人口"),
                ]),
            ],
            location=LocationRef(doc_id="template", sheet="Sheet1", table_index=0),
        )
        doc = CanonicalDocument("template", file=None, doc_type="xlsx", tables=[table])  # type: ignore[arg-type]

        spec = DefaultTemplateAnalyzer().analyze(doc)

        target = spec.target_tables[0]
        self.assertEqual(target.anchor.row_index, 1)
        self.assertEqual([field.field_name for field in target.schema], ["城市", "GDP", "人口"])
        self.assertEqual(target.schema[1].data_type, "number")


class FillRunReportTests(unittest.TestCase):
    def test_writes_fill_run_report_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            class Result:
                fill_result = FillResult(
                    output_doc_id="template",
                    output_path="out.xlsx",
                    written_cells=[],
                    warnings=["warning-one"],
                )
                verification_report = VerificationReport(
                    task_id="task-1",
                    status="warning",
                    summary="summary",
                    checks=[VerificationCheck("check", "warning", "message")],
                )
                debug = {"record_count": 1}

            path = _write_fill_run_report(Path(tmp), "task-1", Result())
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(payload["task_id"], "task-1")
        self.assertEqual(payload["verification_status"], "warning")
        self.assertEqual(payload["debug"]["record_count"], 1)


if __name__ == "__main__":
    unittest.main()
