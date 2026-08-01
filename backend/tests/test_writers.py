from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from docnexus.ai.table_engine.core.models import (  # noqa: E402
    CanonicalDocument,
    FieldSpec,
    FileAsset,
    StructuredRecord,
    TargetTableSpec,
    TemplateSpec,
)
from docnexus.ai.table_engine.writers import XlsxWriter  # noqa: E402
from openpyxl import Workbook, load_workbook  # noqa: E402


class XlsxWriterTests(unittest.TestCase):
    def test_formula_cells_inherit_source_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            template_path = Path(tmp) / "template.xlsx"
            workbook = Workbook()
            workbook.active.append(["区域", "净收入（万元）", "成本（万元）", "毛利（万元）"])
            workbook.save(template_path)
            template_doc = CanonicalDocument(
                doc_id="template",
                file=FileAsset("template", str(template_path), "template.xlsx", "xlsx", "template", None, template_path.stat().st_size),
                doc_type="xlsx",
            )
            template_spec = TemplateSpec(
                template_doc_id="template",
                target_tables=[TargetTableSpec("table-1", "region", schema=[
                    FieldSpec("region", "区域", "区域", "string", True),
                    FieldSpec("income", "净收入（万元）", "收入", "number", True),
                    FieldSpec("cost", "成本（万元）", "成本", "number", True),
                    FieldSpec("gross", "毛利（万元）", "毛利", "number", True),
                ])],
            )
            records = [StructuredRecord(
                "r1",
                "table-1",
                values={"区域": "华东", "净收入（万元）": 100, "成本（万元）": 60, "毛利（万元）": None},
                field_sources={"区域": ["e0"], "净收入（万元）": ["e1"], "成本（万元）": ["e2"]},
            )]

            result = XlsxWriter().write(template_doc, template_spec, records)

            gross_trace = next(cell for cell in result.written_cells if cell.field_name == "毛利（万元）")
            self.assertEqual(gross_trace.value, "=B2-C2")
            self.assertEqual(gross_trace.evidence_ids, ["e1", "e2"])

    def test_numeric_strings_are_written_as_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            template_path = Path(tmp) / "template.xlsx"
            workbook = Workbook()
            workbook.active.append(["序号", "姓名"])
            workbook.save(template_path)
            template_doc = CanonicalDocument(
                doc_id="template",
                file=FileAsset("template", str(template_path), "template.xlsx", "xlsx", "template", None, template_path.stat().st_size),
                doc_type="xlsx",
            )
            template_spec = TemplateSpec(
                template_doc_id="template",
                target_tables=[TargetTableSpec("table-1", "people", schema=[
                    FieldSpec("sequence", "序号", "序号", "number", True),
                    FieldSpec("name", "姓名", "姓名", "string", True),
                ])],
            )
            records = [StructuredRecord("r1", "table-1", values={"序号": "1", "姓名": "陈雨桐"})]

            result = XlsxWriter().write(template_doc, template_spec, records)

            self.assertEqual(load_workbook(result.output_path).active["A2"].value, 1)

    def test_generated_sequence_inherits_record_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            template_path = Path(tmp) / "template.xlsx"
            workbook = Workbook()
            workbook.active.append(["序号", "姓名"])
            workbook.save(template_path)
            template_doc = CanonicalDocument(
                doc_id="template",
                file=FileAsset("template", str(template_path), "template.xlsx", "xlsx", "template", None, template_path.stat().st_size),
                doc_type="xlsx",
            )
            template_spec = TemplateSpec(
                template_doc_id="template",
                target_tables=[TargetTableSpec("table-1", "people", schema=[
                    FieldSpec("sequence", "序号", "序号", "number", True),
                    FieldSpec("name", "姓名", "姓名", "string", True),
                ])],
            )
            records = [StructuredRecord(
                "r1",
                "table-1",
                values={"序号": None, "姓名": "陈雨桐"},
                field_sources={"姓名": ["person-row-1"]},
            )]

            result = XlsxWriter().write(template_doc, template_spec, records)

            sequence_trace = next(cell for cell in result.written_cells if cell.field_name == "序号")
            self.assertEqual(sequence_trace.evidence_ids, ["person-row-1"])

    def test_date_datetime_values_are_written_without_time_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            template_path = work / "template.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.append(["国家/地区", "日期", "病例数"])
            wb.save(template_path)

            template_doc = CanonicalDocument(
                doc_id="template",
                file=FileAsset(
                    id="template",
                    path=str(template_path),
                    name="template.xlsx",
                    ext="xlsx",
                    role="template",
                    mime_type=None,
                    size=template_path.stat().st_size,
                ),
                doc_type="xlsx",
            )
            template_spec = TemplateSpec(
                template_doc_id="template",
                target_tables=[
                    TargetTableSpec(
                        "table-1",
                        "covid",
                        schema=[
                            FieldSpec("country", "国家/地区", "国家地区", "string", True),
                            FieldSpec("date", "日期", "日期", "date", True),
                            FieldSpec("cases", "病例数", "病例数", "number", False),
                        ],
                    )
                ],
            )
            records = [
                StructuredRecord(
                    "r1",
                    "table-1",
                    values={"国家/地区": "Albania", "日期": datetime(2020, 2, 25), "病例数": 1},
                )
            ]

            result = XlsxWriter().write(template_doc, template_spec, records)
            out = load_workbook(result.output_path, data_only=True)
            value = out.active["B2"].value

            self.assertEqual(value, "2020-02-25")

    def test_daily_records_keep_date_identity_and_do_not_mutate_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            template_path = work / "template.xlsx"
            workbook = Workbook()
            workbook.active.append(["城市", "日期", "AQI", "PM2.5"])
            workbook.save(template_path)
            template_doc = CanonicalDocument(
                doc_id="template",
                file=FileAsset("template", str(template_path), "template.xlsx", "xlsx", "template", None, template_path.stat().st_size),
                doc_type="xlsx",
            )
            template_spec = TemplateSpec(
                template_doc_id="template",
                target_tables=[TargetTableSpec(
                    "table-1",
                    "air",
                    schema=[
                        FieldSpec("city", "城市", "城市", "string", True),
                        FieldSpec("date", "日期", "日期", "date", True),
                        FieldSpec("aqi", "AQI", "aqi", "number", True),
                        FieldSpec("pm", "PM2.5", "pm2.5", "number", True),
                    ],
                )],
            )
            records = [
                StructuredRecord("r1", "table-1", values={"城市": "北京市", "日期": "2026-06-04", "AQI": 160, "PM2.5": 55}),
                StructuredRecord("r2", "table-1", values={"城市": "北京市", "日期": "2026-06-02", "AQI": 130, "PM2.5": 40}),
            ]

            result = XlsxWriter().write(template_doc, template_spec, records)
            output = load_workbook(result.output_path, data_only=True).active

            self.assertEqual(len(result.written_cells), 8)
            self.assertEqual(output["B2"].value, "2026-06-04")
            self.assertEqual(output["B3"].value, "2026-06-02")
            self.assertEqual(records[0].values["日期"], "2026-06-04")

    def test_consolidation_preserves_requested_order_across_confidence_levels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            template_path = work / "template.xlsx"
            workbook = Workbook()
            workbook.active.append(["城市", "日期", "AQI"])
            workbook.save(template_path)
            template_doc = CanonicalDocument(
                doc_id="template",
                file=FileAsset(
                    "template", str(template_path), "template.xlsx", "xlsx", "template", None,
                    template_path.stat().st_size,
                ),
                doc_type="xlsx",
            )
            template_spec = TemplateSpec(
                template_doc_id="template",
                target_tables=[TargetTableSpec(
                    "table-1",
                    "air",
                    schema=[
                        FieldSpec("city", "城市", "城市", "string", True),
                        FieldSpec("date", "日期", "日期", "date", True),
                        FieldSpec("aqi", "AQI", "aqi", "number", True),
                    ],
                )],
            )
            records = [
                StructuredRecord(
                    "r1", "table-1", values={"城市": "北京市", "日期": "2026-06-04", "AQI": 160}, confidence=0.9,
                ),
                StructuredRecord(
                    "r2", "table-1", values={"城市": "北京市", "日期": "2026-06-02", "AQI": 130}, confidence=0.6,
                ),
                StructuredRecord(
                    "r3", "table-1", values={"城市": "北京市", "日期": "2026-06-07", "AQI": 125}, confidence=0.8,
                ),
            ]

            result = XlsxWriter().write(template_doc, template_spec, records)
            output = load_workbook(result.output_path, data_only=True).active

            self.assertEqual([output.cell(row, 3).value for row in range(2, 5)], [160, 130, 125])


if __name__ == "__main__":
    unittest.main()
