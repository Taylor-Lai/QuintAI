from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from any2table.core.models import (  # noqa: E402
    CanonicalDocument,
    DocumentBlock,
    EvidenceItem,
    EvidencePack,
    FieldSpec,
    FileAsset,
    LocationRef,
    TargetTableSpec,
    TemplateSpec,
)
from any2table.extractors import _extract_records_from_row_evidence  # noqa: E402
from any2table.planners import DefaultTaskPlanner  # noqa: E402


def _asset(asset_id: str, role: str = "source") -> FileAsset:
    return FileAsset(
        id=asset_id,
        path=f"/tmp/{asset_id}.txt",
        name=f"{asset_id}.txt",
        ext="txt",
        role=role,
        mime_type=None,
        size=1,
    )


def _request_doc(text: str) -> CanonicalDocument:
    location = LocationRef(doc_id="request", paragraph_index=0)
    return CanonicalDocument(
        doc_id="request",
        file=_asset("request", role="user_request"),
        doc_type="txt",
        blocks=[
            DocumentBlock(
                block_id="request#block-0",
                block_type="paragraph",
                text=text,
                location=location,
            )
        ],
    )


def _template_spec() -> TemplateSpec:
    fields = [
        FieldSpec("city", "\u57ce\u5e02", "\u57ce\u5e02", "string", False),
        FieldSpec("date", "\u65e5\u671f", "\u65e5\u671f", "date", False),
        FieldSpec("aqi", "AQI", "aqi", "number", False),
        FieldSpec("pm25", "PM2.5", "pm25", "number", False),
    ]
    return TemplateSpec(
        template_doc_id="template",
        target_tables=[
            TargetTableSpec(
                target_table_id="table-1",
                logical_name="\u7a7a\u6c14\u8d28\u91cf",
                schema=fields,
            )
        ],
    )


class ComplexTaskPlanningTests(unittest.TestCase):
    def test_planner_extracts_complex_request_constraints(self) -> None:
        request = (
            "\u8bf7\u7b5b\u9009\u5317\u4eac\u5e022026\u5e746\u67081\u65e5"
            "\u81f32026\u5e746\u67087\u65e5\u7684\u6570\u636e\uff0c"
            "AQI\u5927\u4e8e100\uff0c\u6309AQI\u964d\u5e8f\u53d6\u524d2\uff0c"
            "\u53ea\u586b\u5199\u65e5\u671f\u548cAQI\u3002"
        )

        task_spec = DefaultTaskPlanner().plan(_request_doc(request), _template_spec(), [])
        constraints = {(c.kind, c.field, c.operator): c.value for c in task_spec.constraints}

        self.assertEqual(task_spec.task_policy, "all_dates")
        self.assertEqual(
            constraints[("date_range", "\u65e5\u671f", "between")],
            {"start": "2026-06-01", "end": "2026-06-07"},
        )
        self.assertEqual(constraints[("entity", "\u57ce\u5e02", "equals")], "\u5317\u4eac\u5e02")
        self.assertEqual(constraints[("field_filter", "AQI", ">")], 100)
        self.assertEqual(constraints[("sort", "AQI", "desc")], "AQI")
        self.assertEqual(constraints[("limit", None, "top")], 2)

    def test_row_extractor_applies_complex_filters_sort_and_limit(self) -> None:
        request = "\u8bf7\u7b5b\u9009\u5317\u4eac\u5e02\uff0cAQI\u5927\u4e8e100\uff0c\u6309AQI\u964d\u5e8f\u53d6\u524d2\u3002"
        template_spec = _template_spec()
        task_spec = DefaultTaskPlanner().plan(_request_doc(request), template_spec, [])
        target_table = template_spec.target_tables[0]
        evidence_pack = EvidencePack(
            task_id="task",
            items=[
                EvidenceItem("r1", "row", "doc", {"\u57ce\u5e02": "\u5317\u4eac\u5e02", "\u65e5\u671f": "2026-06-01", "AQI": 90, "PM2.5": 30}),
                EvidenceItem("r2", "row", "doc", {"\u57ce\u5e02": "\u5317\u4eac\u5e02", "\u65e5\u671f": "2026-06-02", "AQI": 130, "PM2.5": 40}),
                EvidenceItem("r3", "row", "doc", {"\u57ce\u5e02": "\u4e0a\u6d77\u5e02", "\u65e5\u671f": "2026-06-03", "AQI": 180, "PM2.5": 70}),
                EvidenceItem("r4", "row", "doc", {"\u57ce\u5e02": "\u5317\u4eac\u5e02", "\u65e5\u671f": "2026-06-04", "AQI": 160, "PM2.5": 55}),
                EvidenceItem("r5", "row", "doc", {"\u57ce\u5e02": "\u5317\u4eac\u5e02", "\u65e5\u671f": "2026-06-05", "AQI": 120, "PM2.5": 35}),
            ],
        )

        records = _extract_records_from_row_evidence(target_table, task_spec, evidence_pack)

        self.assertEqual([record.values["AQI"] for record in records], [160, 130])
        self.assertTrue(all(record.values["\u57ce\u5e02"] == "\u5317\u4eac\u5e02" for record in records))


if __name__ == "__main__":
    unittest.main()
