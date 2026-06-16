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
from any2table.candidates.builders import (  # noqa: E402
    _clean_city_value,
    has_required_row_identity,
    identity_fields_for_target_fields,
)
from any2table.planners import DefaultTaskPlanner, _candidate_entity_values  # noqa: E402


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

    def test_multi_city_request_splits_entity_values(self) -> None:
        request = (
            "\u8bf7\u6839\u636e\u6e90\u6587\u4ef6\u586b\u5199\u6a21\u677f\uff0c"
            "\u4fdd\u7559\u5317\u4eac\u5e02\u548c\u4e0a\u6d77\u5e02\uff0c"
            "\u6309GDP\u603b\u91cf\u964d\u5e8f\u586b\u5199\u57ce\u5e02\u540d\u3002"
        )

        self.assertEqual(
            _candidate_entity_values(request, "\u57ce\u5e02"),
            ["\u5317\u4eac\u5e02", "\u4e0a\u6d77\u5e02"],
        )

    def test_city_name_is_valid_row_identity(self) -> None:
        fields = [
            "\u57ce\u5e02\u540d",
            "GDP\u603b\u91cf\uff08\u4ebf\u5143\uff09",
            "\u5e38\u4f4f\u4eba\u53e3\uff08\u4e07\u4eba\uff09",
        ]

        self.assertEqual(identity_fields_for_target_fields(fields), ["\u57ce\u5e02\u540d"])
        self.assertTrue(has_required_row_identity({"\u57ce\u5e02\u540d": "\u5317\u4eac\u5e02"}, "city"))

    def test_city_value_cleanup_removes_sentence_tail(self) -> None:
        self.assertEqual(_clean_city_value("\u4e0a\u6d77\u4ee5"), "\u4e0a\u6d77\u5e02")
        self.assertEqual(_clean_city_value("\u6df1\u5733\u4ee5GDP\u589e\u901f\u9886\u5148"), "\u6df1\u5733\u5e02")
        self.assertEqual(_clean_city_value("\u91cd\u5e86\u51ed\u501f\u4ea7\u4e1a\u5347\u7ea7"), "\u91cd\u5e86\u5e02")
        self.assertEqual(_clean_city_value("\u6000\u5316"), "\u6000\u5316")

    def test_country_daily_rows_are_grouped_then_sorted_by_date(self) -> None:
        fields = [
            FieldSpec("country", "\u56fd\u5bb6/\u5730\u533a", "\u56fd\u5bb6\u5730\u533a", "string", True),
            FieldSpec("continent", "\u5927\u6d32", "\u5927\u6d32", "string", False),
            FieldSpec("date", "\u65e5\u671f", "\u65e5\u671f", "date", True),
            FieldSpec("cases", "\u75c5\u4f8b\u6570", "\u75c5\u4f8b\u6570", "number", False),
        ]
        template_spec = TemplateSpec(
            template_doc_id="template",
            target_tables=[TargetTableSpec("covid", "\u75ab\u60c5", schema=fields)],
        )
        request = "\u6309\u65e5\u671f\u5347\u5e8f\u586b\u5199\uff0c\u540c\u4e00\u56fd\u5bb6\u653e\u5728\u4e00\u8d77\u3002"
        task_spec = DefaultTaskPlanner().plan(_request_doc(request), template_spec, [])
        target_table = template_spec.target_tables[0]
        evidence_pack = EvidencePack(
            task_id="task",
            items=[
                EvidenceItem("r1", "row", "doc", {"\u56fd\u5bb6/\u5730\u533a": "Algeria", "\u5927\u6d32": "Africa", "\u65e5\u671f": "2020-02-26", "\u75c5\u4f8b\u6570": 2}),
                EvidenceItem("r2", "row", "doc", {"\u56fd\u5bb6/\u5730\u533a": "Albania", "\u5927\u6d32": "Europe", "\u65e5\u671f": "2020-02-27", "\u75c5\u4f8b\u6570": 3}),
                EvidenceItem("r3", "row", "doc", {"\u56fd\u5bb6/\u5730\u533a": "Algeria", "\u5927\u6d32": "Africa", "\u65e5\u671f": "2020-02-25", "\u75c5\u4f8b\u6570": 1}),
                EvidenceItem("r4", "row", "doc", {"\u56fd\u5bb6/\u5730\u533a": "Albania", "\u5927\u6d32": "Europe", "\u65e5\u671f": "2020-02-25", "\u75c5\u4f8b\u6570": 1}),
            ],
        )

        records = _extract_records_from_row_evidence(target_table, task_spec, evidence_pack)

        self.assertEqual(
            [(record.values["\u56fd\u5bb6/\u5730\u533a"], record.values["\u65e5\u671f"]) for record in records],
            [
                ("Albania", "2020-02-25"),
                ("Albania", "2020-02-27"),
                ("Algeria", "2020-02-25"),
                ("Algeria", "2020-02-26"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
