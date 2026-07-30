import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from docnexus.ai.document_operations import (
    FormatAction,
    _apply_insert_action,
    _apply_replace_action,
    _apply_structure_action,
    _build_rule_based_table_action,
    _unresolved_action_reports,
    build_rule_based_plan,
)
from docnexus.ai.information_extraction import merge_chunk_extractions
from docx import Document


class DocumentOperationModelTests(unittest.TestCase):
    def test_format_action_supports_non_format_operations(self) -> None:
        action = FormatAction(
            operation="replace",
            target_paragraph_index=-1,
            target_text="旧文本",
            content="新文本",
        )

        self.assertEqual(action.operation, "replace")
        self.assertEqual(action.target_text, "旧文本")
        self.assertEqual(action.content, "新文本")

    def test_rule_plan_splits_complex_command(self) -> None:
        plan = build_rule_based_plan("把第一段加粗并设为红色，然后将“旧标题”替换为“新标题”，最后添加目录")

        operations = [action.operation for action in plan.actions]
        self.assertIn("format", operations)
        self.assertIn("replace", operations)
        self.assertIn("structure", operations)
        self.assertEqual(plan.actions[0].target_paragraph_index, 0)
        self.assertEqual(plan.actions[0].color_hex, "#FF0000")

    def test_rule_plan_inherits_target_for_split_style_command(self) -> None:
        plan = build_rule_based_plan("把第一段加粗并且设为红色")

        self.assertEqual(len(plan.actions), 1)
        self.assertEqual(plan.actions[0].operation, "format")
        self.assertEqual(plan.actions[0].target_paragraph_index, 0)
        self.assertTrue(plan.actions[0].bold)
        self.assertEqual(plan.actions[0].color_hex, "#FF0000")

    def test_rule_plan_does_not_treat_color_changes_as_text_replacement(self) -> None:
        plan = build_rule_based_plan(
            "\u5168\u6587\u5c45\u4e2d\uff1b\u5c06\u6807\u9898\u8bbe\u7f6e\u4e3a\u52a0\u7c97\u5e76\u6539\u6210\u7ea2\u8272\uff1b"
            "\u5c06\u7b2c2\u6bb5\u8bbe\u7f6e\u4e3a16\u53f7\u5e76\u6539\u6210\u84dd\u8272\u3002"
        )

        self.assertNotIn("replace", [action.operation for action in plan.actions])
        self.assertTrue(any(action.target_paragraph_index == -1 and action.alignment == "center" for action in plan.actions))
        self.assertTrue(
            any(
                action.target_paragraph_index == 0 and action.bold and action.color_hex == "#FF0000"
                for action in plan.actions
            )
        )
        self.assertTrue(
            any(
                action.target_paragraph_index == 1 and action.font_size == 16 and action.color_hex == "#0000FF"
                for action in plan.actions
            )
        )

    def test_replace_action_is_idempotent_when_content_already_exists(self) -> None:
        doc = Document()
        doc.add_paragraph("第 29 周产品例会纪要")

        changed = _apply_replace_action(
            doc,
            FormatAction(operation="replace", target_text="标题", content="第 29 周产品例会纪要"),
        )

        self.assertEqual(changed, 1)

        quoted_changed = _apply_replace_action(
            doc,
            FormatAction(operation="replace", target_text="标题", content="“第 29 周产品例会纪要”"),
        )
        self.assertEqual(quoted_changed, 1)

    def test_insert_action_is_idempotent_when_content_already_exists(self) -> None:
        doc = Document()
        doc.add_paragraph("下次会议：2026 年 7 月 28 日 10:00")

        changed = _apply_insert_action(
            doc,
            FormatAction(operation="insert", content="下次会议：2026 年 7 月 28 日 10:00"),
        )

        self.assertEqual(changed, 1)
        self.assertEqual(
            [p.text for p in doc.paragraphs],
            ["下次会议：2026 年 7 月 28 日 10:00"],
        )

    def test_structure_action_builds_table_and_replaces_source_rows(self) -> None:
        doc = Document()
        doc.add_paragraph("待办事项")
        doc.add_paragraph("林晓宇负责准备演示数据，周四完成。")
        doc.add_paragraph("陈嘉负责修复移动端布局，周三完成。")

        changed = _apply_structure_action(
            doc,
            FormatAction(
                operation="structure",
                target_text="table",
                content="负责人|事项|截止日期\n林晓宇|准备演示数据|周四完成\n陈嘉|修复移动端布局|周三完成",
            ),
        )

        self.assertEqual(changed, 3)
        self.assertEqual(len(doc.tables), 1)
        self.assertEqual(
            [[cell.text for cell in row.cells] for row in doc.tables[0].rows],
            [
                ["负责人", "事项", "截止日期"],
                ["林晓宇", "准备演示数据", "周四完成"],
                ["陈嘉", "修复移动端布局", "周三完成"],
            ],
        )
        self.assertNotIn("林晓宇负责准备演示数据，周四完成。", [p.text for p in doc.paragraphs])

    def test_rule_based_table_action_uses_section_rows(self) -> None:
        doc = Document()
        doc.add_paragraph("待办事项")
        doc.add_paragraph("林晓宇负责准备演示数据，周四完成。")
        doc.add_paragraph("陈嘉负责修复移动端布局，周三完成。")

        action = _build_rule_based_table_action(
            "把待办事项整理成负责人、事项、截止日期三列表格",
            doc,
        )

        self.assertIsNotNone(action)
        assert action is not None
        self.assertEqual(action.target_text, "table")
        self.assertEqual(
            action.content,
            "负责人|事项|截止日期\n林晓宇|准备演示数据|周四完成\n陈嘉|修复移动端布局|周三完成",
        )

    def test_structure_action_accepts_comma_delimited_llm_content_idempotently(self) -> None:
        doc = Document()
        first_action = FormatAction(
            operation="structure",
            target_text="table",
            content="负责人|事项|截止日期\n林晓宇|准备演示数据|周四完成",
        )
        duplicate_action = FormatAction(
            operation="structure",
            target_text="table",
            content="负责人,事项,截止日期\n林晓宇,准备演示数据,周四完成",
        )

        self.assertEqual(_apply_structure_action(doc, first_action), 2)
        self.assertEqual(_apply_structure_action(doc, duplicate_action), 2)
        self.assertEqual(len(doc.tables), 1)

    def test_each_zero_effect_action_remains_unresolved(self) -> None:
        reports = [
            {"operation": "replace", "affected_count": 1},
            {"operation": "replace", "affected_count": 0},
            {"operation": "structure", "affected_count": 0},
        ]

        self.assertEqual(
            _unresolved_action_reports(reports),
            [
                {"operation": "replace", "affected_count": 0},
                {"operation": "structure", "affected_count": 0},
            ],
        )


class InformationExtractionMetadataTests(unittest.TestCase):
    def test_merge_outputs_normalized_values_and_confidence(self) -> None:
        chunks = [{"chunk_id": 0, "start": 0, "end": 30, "text": "项目日期为2026年5月26日，预算100万元。"}]
        result = merge_chunk_extractions(
            [{"项目日期": "2026年5月26日", "预算": "100万元"}],
            chunks,
            ["项目日期", "预算"],
            chunks[0]["text"],
        )

        self.assertEqual(result["_meta"]["normalized"]["项目日期"], "2026-05-26")
        self.assertEqual(result["_meta"]["normalized"]["预算"], 100)
        self.assertGreaterEqual(result["_meta"]["confidence"]["项目日期"], 0.7)
        self.assertEqual(result["_meta"]["validation"]["项目日期"]["status"], "pass")
        self.assertEqual(result["_meta"]["validation"]["预算"]["expected_type"], "number")
        self.assertEqual(result["_meta"]["candidates"]["预算"], ["100万元"])

    def test_conflict_lowers_confidence(self) -> None:
        chunks = [
            {"chunk_id": 0, "start": 0, "end": 10, "text": "负责人张三"},
            {"chunk_id": 1, "start": 10, "end": 20, "text": "负责人李四"},
        ]
        result = merge_chunk_extractions(
            [{"负责人": "张三"}, {"负责人": "李四"}],
            chunks,
            ["负责人"],
            "负责人张三负责人李四",
        )

        self.assertEqual(result["负责人"], "张三")
        self.assertEqual(result["_meta"]["conflicts"]["负责人"], ["张三", "李四"])
        self.assertEqual(result["_meta"]["confidence"]["负责人"], 0.55)
        self.assertEqual(result["_meta"]["validation"]["负责人"]["status"], "conflict")


class UnicodeInformationExtractionFallbackTests(unittest.TestCase):
    def test_missing_unicode_date_is_filled_by_rule_fallback(self) -> None:
        full_text = "项目名称：全球疫情分析\n截止日期：2026年7月15日\n负责人：李雷"
        chunks = [{"chunk_id": 0, "start": 0, "end": len(full_text), "text": full_text}]
        result = merge_chunk_extractions(
            [{"项目名称": "全球疫情分析", "截止日期": "未找到"}],
            chunks,
            ["项目名称", "截止日期"],
            full_text,
        )

        self.assertEqual(result["截止日期"], "2026-07-15")
        self.assertEqual(result["_meta"]["normalized"]["截止日期"], "2026-07-15")
        self.assertEqual(result["_meta"]["validation"]["截止日期"]["status"], "pass")
        self.assertEqual(result["_meta"]["evidence"]["截止日期"]["strategy"], "date_regex_fallback")


if __name__ == "__main__":
    unittest.main()
