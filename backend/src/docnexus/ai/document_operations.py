"""Natural-language Word document operations."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, model_validator

from docnexus.ai.llm import get_chat_llm

logger = logging.getLogger(__name__)

def _schema_classes():
    try:
        from docnexus.ai.contracts import DocumentOperationOutput
    except ImportError:  # pragma: no cover - local package fallback
        from .contracts import DocumentOperationOutput
    return DocumentOperationOutput


class FormatAction(BaseModel):
    operation: str = Field("format", description="操作类型: format, insert, delete, replace, extract, structure")
    target_paragraph_index: int = Field(-1, description="要修改的段落索引(从0开始，如果是全文则填 -1)")
    target_text: str | None = Field(None, description="要查找或操作的目标文本")
    content: str | None = Field(None, description="插入内容、替换内容或结构内容")
    font_size: int | None = Field(None, description="字号大小(数字，如 14)")
    bold: bool | None = Field(None, description="是否加粗")
    color_hex: str | None = Field(None, description="十六进制颜色码，如 '#FF0000' 代表红色")
    alignment: str | None = Field(None, description="对齐方式: 'left', 'center', 'right'")


class FormatPlan(BaseModel):
    actions: list[FormatAction] = Field(default_factory=list, description="格式修改动作列表，若无需修改则为空列表")

    @model_validator(mode="before")
    @classmethod
    def _normalize_actions(cls, data):
        if isinstance(data, dict) and "action" in data and "actions" not in data:
            val = data["action"]
            data["actions"] = val if isinstance(val, list) else []
        return data


PARAGRAPH_INDEX_WORDS = {
    "一": 0,
    "二": 1,
    "三": 2,
    "四": 3,
    "五": 4,
    "六": 5,
    "七": 6,
    "八": 7,
    "九": 8,
    "十": 9,
}
COLOR_MAP = {
    "红": "#FF0000",
    "红色": "#FF0000",
    "蓝": "#0000FF",
    "蓝色": "#0000FF",
    "绿": "#008000",
    "绿色": "#008000",
    "黑": "#000000",
    "黑色": "#000000",
}


def _split_command(command: str) -> list[str]:
    parts = re.split(r"[；;。\n]+|然后|并且|同时|最后|接着|随后|再", command)
    return [part.strip(" ，,") for part in parts if part.strip(" ，,")]


def _infer_target_paragraph_index(text: str) -> int | None:
    if any(token in text for token in ("全文", "全部", "所有")):
        return -1
    if any(token in text for token in ("标题", "题目")):
        return 0
    digit_match = re.search(r"第\s*(\d+)\s*段", text)
    if digit_match:
        return max(int(digit_match.group(1)) - 1, 0)
    cn_match = re.search(r"第\s*([一二三四五六七八九十])\s*段", text)
    if cn_match:
        return PARAGRAPH_INDEX_WORDS.get(cn_match.group(1), -1)
    return None


def _infer_alignment(text: str) -> str | None:
    if "居中" in text or "居中对齐" in text:
        return "center"
    if "右对齐" in text or "靠右" in text:
        return "right"
    if "左对齐" in text or "靠左" in text:
        return "left"
    return None


def _infer_color(text: str) -> str | None:
    hex_match = re.search(r"#?[0-9a-fA-F]{6}", text)
    if hex_match:
        color = hex_match.group(0)
        return color if color.startswith("#") else f"#{color}"
    for token, color in COLOR_MAP.items():
        if token in text:
            return color
    return None


def _infer_font_size(text: str) -> int | None:
    match = re.search(r"(\d+)\s*(?:号|pt|磅)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _extract_quoted_pair(text: str) -> tuple[str | None, str | None]:
    quoted = re.findall(r"[“\"']([^”\"']+)[”\"']", text)
    if len(quoted) >= 2:
        return quoted[0], quoted[1]
    return None, None


def _is_formatting_change(text: str, replacement: str | None) -> bool:
    """Distinguish style changes such as ``改成红色`` from text replacement."""
    if not replacement:
        return False
    formatting_tokens = (
        "加粗",
        "取消加粗",
        "字体",
        "字号",
        "颜色",
        "红色",
        "蓝色",
        "绿色",
        "黑色",
        "居中",
        "左对齐",
        "右对齐",
        "号",
        "磅",
        "pt",
    )
    return any(token.lower() in text.lower() for token in formatting_tokens) and any(
        token.lower() in replacement.lower() for token in formatting_tokens
    )


def build_rule_based_plan(command: str) -> FormatPlan:
    actions: list[FormatAction] = []
    last_target_index = -1
    for part in _split_command(command):
        explicit_target_index = _infer_target_paragraph_index(part)
        target_index = explicit_target_index if explicit_target_index is not None else last_target_index
        if explicit_target_index is not None:
            last_target_index = explicit_target_index
        if "替换" in part or "改成" in part or "改为" in part:
            old_text, new_text = _extract_quoted_pair(part)
            if old_text is None:
                match = re.search(r"(?:把|将)?(.+?)(?:替换为|替换成|改成|改为)(.+)", part)
                if match:
                    old_text = match.group(1).strip(" ，,。")
                    new_text = match.group(2).strip(" ，,。")
            if old_text and new_text and not _is_formatting_change(part, new_text):
                actions.append(FormatAction(operation="replace", target_paragraph_index=target_index, target_text=old_text, content=new_text))
                continue
        if "删除" in part or "去掉" in part:
            target_text = None
            quoted = re.findall(r"[“\"']([^”\"']+)[”\"']", part)
            if quoted:
                target_text = quoted[0]
            actions.append(FormatAction(operation="delete", target_paragraph_index=target_index, target_text=target_text))
            continue
        if "插入" in part or "添加" in part or "新增" in part:
            quoted = re.findall(r"[“\"']([^”\"']+)[”\"']", part)
            content = quoted[0] if quoted else None
            if content:
                if "开头" in part or "前面" in part:
                    target_index = 0
                elif "末尾" in part or "最后" in part:
                    target_index = -2
                actions.append(FormatAction(operation="insert", target_paragraph_index=target_index, content=content))
                continue
        if "目录" in part:
            actions.append(FormatAction(operation="structure", target_paragraph_index=-1, target_text="目录"))
            continue
        if "页眉" in part:
            quoted = re.findall(r"[“\"']([^”\"']+)[”\"']", part)
            actions.append(FormatAction(operation="structure", target_paragraph_index=-1, target_text="页眉", content=quoted[0] if quoted else None))
            continue
        if "提取" in part or "抽取" in part:
            actions.append(FormatAction(operation="extract", target_paragraph_index=target_index))
            continue

        bold = True if "加粗" in part else None
        font_size = _infer_font_size(part)
        color_hex = _infer_color(part)
        alignment = _infer_alignment(part)
        if any(value is not None for value in (bold, font_size, color_hex, alignment)):
            new_action = FormatAction(
                operation="format",
                target_paragraph_index=target_index,
                bold=bold,
                font_size=font_size,
                color_hex=color_hex,
                alignment=alignment,
            )
            if actions and actions[-1].operation == "format" and actions[-1].target_paragraph_index == target_index:
                previous = actions[-1]
                previous.bold = new_action.bold if new_action.bold is not None else previous.bold
                previous.font_size = new_action.font_size if new_action.font_size is not None else previous.font_size
                previous.color_hex = new_action.color_hex if new_action.color_hex is not None else previous.color_hex
                previous.alignment = new_action.alignment if new_action.alignment is not None else previous.alignment
            else:
                actions.append(new_action)
    return FormatPlan(actions=actions)


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def _infer_unicode_target_paragraph_index(text: str) -> int | None:
    if _contains_any(text, ("\u5168\u6587", "\u5168\u90e8", "\u6240\u6709")):
        return -1
    if _contains_any(text, ("\u6807\u9898", "\u9898\u76ee")):
        return 0
    if _contains_any(text, ("\u7b2c\u4e00\u6bb5", "\u9996\u6bb5")):
        return 0
    match = re.search(r"\u7b2c\s*(\d+)\s*\u6bb5", text)
    if match:
        return max(int(match.group(1)) - 1, 0)
    return None


def _infer_unicode_alignment(text: str) -> str | None:
    if _contains_any(text, ("\u5c45\u4e2d", "\u5c45\u4e2d\u5bf9\u9f50")):
        return "center"
    if _contains_any(text, ("\u53f3\u5bf9\u9f50", "\u9760\u53f3")):
        return "right"
    if _contains_any(text, ("\u5de6\u5bf9\u9f50", "\u9760\u5de6")):
        return "left"
    return None


def _infer_unicode_color(text: str) -> str | None:
    hex_match = re.search(r"#?[0-9a-fA-F]{6}", text)
    if hex_match:
        color = hex_match.group(0)
        return color if color.startswith("#") else f"#{color}"
    if _contains_any(text, ("\u7ea2\u8272", "\u7ea2")):
        return "#FF0000"
    if _contains_any(text, ("\u84dd\u8272", "\u84dd")):
        return "#0000FF"
    if _contains_any(text, ("\u7eff\u8272", "\u7eff")):
        return "#008000"
    if _contains_any(text, ("\u9ed1\u8272", "\u9ed1")):
        return "#000000"
    return None


def _infer_unicode_font_size(text: str) -> int | None:
    match = re.search(r"(\d+)\s*(?:\u53f7|\u78c5|pt)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def build_unicode_rule_based_plan(command: str) -> FormatPlan:
    actions: list[FormatAction] = []
    last_target_index = -1
    parts = re.split(
        r"[\uff0c\u3002\uff1b;\n]+|\u7136\u540e|\u5e76\u4e14|\u540c\u65f6|\u63a5\u7740|\u968f\u540e|\u518d",
        command,
    )
    for raw_part in parts:
        part = raw_part.strip()
        if not part:
            continue
        explicit_target_index = _infer_unicode_target_paragraph_index(part)
        target_index = explicit_target_index if explicit_target_index is not None else last_target_index
        if explicit_target_index is not None:
            last_target_index = explicit_target_index

        bold = True if "\u52a0\u7c97" in part else None
        font_size = _infer_unicode_font_size(part)
        color_hex = _infer_unicode_color(part)
        alignment = _infer_unicode_alignment(part)
        if any(value is not None for value in (bold, font_size, color_hex, alignment)):
            actions.append(
                FormatAction(
                    operation="format",
                    target_paragraph_index=target_index,
                    bold=bold,
                    font_size=font_size,
                    color_hex=color_hex,
                    alignment=alignment,
                )
            )
    return FormatPlan(actions=actions)


def merge_rule_plans(*plans: FormatPlan) -> FormatPlan:
    actions: list[FormatAction] = []
    seen: set[tuple[object, ...]] = set()
    for plan in plans:
        for action in plan.actions:
            key = (
                action.operation,
                action.target_paragraph_index,
                action.target_text,
                action.content,
                action.font_size,
                action.bold,
                action.color_hex,
                action.alignment,
            )
            if key not in seen:
                seen.add(key)
                actions.append(action)
    return FormatPlan(actions=actions)


def _target_paragraphs(doc: Document, action: FormatAction):
    if action.target_paragraph_index == -1:
        return doc.paragraphs
    elif 0 <= action.target_paragraph_index < len(doc.paragraphs):
        return [doc.paragraphs[action.target_paragraph_index]]
    elif action.target_text:
        return [p for p in doc.paragraphs if action.target_text in p.text]
    return []


def _apply_format_action(doc: Document, action: FormatAction) -> int:
    paragraphs = _target_paragraphs(doc, action)
    changed = 0

    for paragraph in paragraphs:
        if action.alignment == "left":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        elif action.alignment == "center":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif action.alignment == "right":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        if not paragraph.runs and paragraph.text:
            text = paragraph.text
            paragraph.clear()
            paragraph.add_run(text)

        for run in paragraph.runs:
            if action.bold is not None:
                run.bold = action.bold
            if action.font_size is not None:
                run.font.size = Pt(action.font_size)
            if action.color_hex:
                hex_color = action.color_hex.lstrip("#")
                if len(hex_color) == 3:
                    hex_color = "".join(c * 2 for c in hex_color)
                if len(hex_color) == 6:
                    run.font.color.rgb = RGBColor(
                        int(hex_color[:2], 16),
                        int(hex_color[2:4], 16),
                        int(hex_color[4:], 16),
                    )
            changed += 1
    return changed


def _apply_insert_action(doc: Document, action: FormatAction) -> int:
    content = (action.content or "").strip()
    if not content:
        return 0
    paragraphs = [line.strip() for line in content.splitlines() if line.strip()] or [content]
    existing_text = {paragraph.text.strip() for paragraph in doc.paragraphs if paragraph.text.strip()}
    pending_paragraphs = [text for text in paragraphs if text not in existing_text]
    if not pending_paragraphs:
        return len(paragraphs)
    if action.target_paragraph_index == -2:
        for text in pending_paragraphs:
            doc.add_paragraph(text)
    elif action.target_paragraph_index == 0 and doc.paragraphs:
        for text in reversed(pending_paragraphs):
            doc.paragraphs[0].insert_paragraph_before(text)
    elif 0 <= action.target_paragraph_index < len(doc.paragraphs):
        anchor = doc.paragraphs[action.target_paragraph_index]
        for text in reversed(pending_paragraphs):
            anchor.insert_paragraph_before(text)
    else:
        for text in pending_paragraphs:
            doc.add_paragraph(text)
    return len(pending_paragraphs)


def _apply_delete_action(doc: Document, action: FormatAction) -> int:
    changed = 0
    target = action.target_text
    for paragraph in _target_paragraphs(doc, action):
        if target:
            if target in paragraph.text:
                paragraph.text = paragraph.text.replace(target, "")
                changed += 1
        else:
            paragraph.clear()
            changed += 1
    return changed


def _apply_replace_action(doc: Document, action: FormatAction) -> int:
    target = action.target_text or ""
    content = action.content or ""
    if not target:
        return 0
    changed = 0
    for paragraph in doc.paragraphs:
        if target in paragraph.text:
            paragraph.text = paragraph.text.replace(target, content)
            changed += 1
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if target in cell.text:
                    cell.text = cell.text.replace(target, content)
                    changed += 1
    # Treat a repeated semantic action as idempotently complete. The LLM plan
    # can overlap with the deterministic safety-net plan (for example, both
    # may rename the title), so the second action should not be reported as a
    # missed edit when the requested content is already present.
    if changed == 0 and content:
        normalized_content = content.strip().strip("“”\"'").strip()
        existing_text = [paragraph.text for paragraph in doc.paragraphs]
        existing_text.extend(cell.text for table in doc.tables for row in table.rows for cell in row.cells)
        if normalized_content and any(normalized_content in text for text in existing_text):
            return 1
    return changed


def _parse_table_content(content: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for raw_line in content.splitlines():
        line = raw_line.strip().strip("|")
        if not line:
            continue
        delimiter = r"\|" if "|" in line else r"[，,]"
        cells = [cell.strip() for cell in re.split(delimiter, line)]
        if len(cells) < 2:
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    if len(rows) < 2:
        return []
    width = len(rows[0])
    if width < 2 or any(len(row) != width for row in rows):
        return []
    return rows


def _build_rule_based_table_action(command: str, doc: Document) -> FormatAction | None:
    if "表格" not in command:
        return None

    header_match = re.search(
        r"(?:整理|转换|转|改).*?成\s*(.+?)(?:[二三四五六七八九十\d]+列)?表格",
        command,
    )
    if not header_match:
        return None
    headers = [value.strip() for value in re.split(r"[、，,/]+", header_match.group(1)) if value.strip()]
    if len(headers) < 2:
        return None

    section_match = re.search(r"(?:把|将)\s*(.+?)(?:整理|转换|转|改).*?表格", command)
    section_name = section_match.group(1).strip(" ，,") if section_match else ""
    paragraphs = list(doc.paragraphs)
    start_index = -1
    if section_name:
        start_index = next(
            (index for index, paragraph in enumerate(paragraphs) if section_name in paragraph.text),
            -1,
        )

    source_rows: list[list[str]] = []
    for paragraph in paragraphs[start_index + 1 :] if start_index >= 0 else paragraphs:
        text = paragraph.text.strip().rstrip("。.")
        if not text:
            continue
        if len(headers) == 3:
            row_match = re.match(r"^(.+?)负责(.+?)[，,]\s*(.+)$", text)
            if row_match:
                source_rows.append([value.strip() for value in row_match.groups()])
                continue
        parts = [value.strip() for value in re.split(r"[，,；;]", text) if value.strip()]
        if len(parts) == len(headers):
            source_rows.append(parts)

    if not source_rows:
        return None
    content = "\n".join("|".join(row) for row in [headers, *source_rows])
    return FormatAction(operation="structure", target_paragraph_index=-1, target_text="table", content=content)


def _remove_paragraph(paragraph) -> None:
    element = paragraph._element
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)


def _apply_table_structure(doc: Document, content: str) -> int:
    rows = _parse_table_content(content)
    if not rows:
        return 0

    for existing_table in doc.tables:
        existing_rows = [[cell.text.strip() for cell in row.cells] for row in existing_table.rows]
        if existing_rows == rows:
            return len(rows)

    # Prefer placing a generated task table directly after the corresponding
    # section heading instead of appending it after unrelated trailing text.
    anchor = next(
        (
            paragraph
            for paragraph in reversed(doc.paragraphs)
            if paragraph.text.strip() and any(token in paragraph.text for token in ("待办", "事项", "任务", "行动项"))
        ),
        doc.paragraphs[-1] if doc.paragraphs else None,
    )

    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = "Table Grid"
    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row):
            cell = table.cell(row_index, column_index)
            cell.text = value
            if row_index == 0:
                for run in cell.paragraphs[0].runs:
                    run.bold = True

    if anchor is not None:
        anchor._p.addnext(table._tbl)

    # Remove source prose that has been represented by a data row. Matching at
    # least two cell values avoids deleting unrelated paragraphs that happen to
    # mention only a person's name or a date.
    for paragraph in list(doc.paragraphs):
        text = paragraph.text.strip()
        if not text or paragraph is anchor:
            continue
        for row in rows[1:]:
            meaningful_cells = [cell for cell in row if len(cell) >= 2]
            if sum(cell in text for cell in meaningful_cells) >= min(2, len(meaningful_cells)):
                _remove_paragraph(paragraph)
                break
    return len(rows)


def _apply_structure_action(doc: Document, action: FormatAction) -> int:
    content = (action.content or "").strip()
    target = (action.target_text or "").strip()
    if target in {"目录", "toc"}:
        doc.add_paragraph("目录", style="Heading 1")
        return 1
    if target in {"标题", "heading"} and content:
        doc.add_heading(content, level=1)
        return 1
    if target in {"页眉", "header"} and content:
        section = doc.sections[0]
        section.header.paragraphs[0].text = content
        return 1
    if target.lower() in {"table", "表格"} and content:
        return _apply_table_structure(doc, content)
    return 0


def _apply_extract_action(doc: Document, action: FormatAction) -> tuple[int, list[str]]:
    paragraphs = _target_paragraphs(doc, action)
    extracted = [paragraph.text for paragraph in paragraphs if paragraph.text.strip()]
    return len(extracted), extracted


def _execute_action(doc: Document, action: FormatAction) -> tuple[str, int, dict[str, object]]:
    operation = (action.operation or "format").lower()
    if operation == "insert":
        changed = _apply_insert_action(doc, action)
        return operation, changed, {}
    if operation == "delete":
        changed = _apply_delete_action(doc, action)
        return operation, changed, {}
    if operation == "replace":
        changed = _apply_replace_action(doc, action)
        return operation, changed, {}
    if operation == "structure":
        changed = _apply_structure_action(doc, action)
        return operation, changed, {}
    if operation == "extract":
        changed, extracted = _apply_extract_action(doc, action)
        return operation, changed, {"extracted_text": extracted[:20]}
    changed = _apply_format_action(doc, action)
    return "format", changed, {}


def _unresolved_action_reports(action_reports: list[dict[str, object]]) -> list[dict[str, object]]:
    return [report for report in action_reports if report["affected_count"] == 0]


def _write_operation_audit(
    doc_path: Path,
    output_path: Path,
    command: str,
    actions: list[FormatAction],
    action_reports: list[dict[str, object]],
    warnings: list[str] | None = None,
) -> Path:
    audit_path = output_path.with_suffix(".operation_audit.json")
    payload = {
        "schema_version": "1.0",
        "source_file": str(doc_path),
        "output_file": str(output_path),
        "command": command,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "action_count": len(actions),
        "actions": action_reports,
        "missed_actions": _unresolved_action_reports(action_reports),
        "warnings": list(warnings or []),
    }
    audit_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return audit_path


def handle_document_operation(input_data):
    output_schema = _schema_classes()
    try:
        doc_path = Path(input_data.file_path)
        if not doc_path.exists():
            return output_schema(status="failed", message=f"文件不存在: {doc_path}")

        doc = Document(doc_path)
        preview_text = "\n".join(
            f"[{i}] {p.text}" for i, p in enumerate(doc.paragraphs[:10]) if p.text.strip()
        )

        rule_plan = merge_rule_plans(
            build_rule_based_plan(input_data.natural_language_cmd),
            build_unicode_rule_based_plan(input_data.natural_language_cmd),
        )
        table_action = _build_rule_based_table_action(input_data.natural_language_cmd, doc)
        if table_action is not None:
            rule_plan.actions.append(table_action)
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "你是一个文档智能操作助手。以下是文档的前几段预览：\n{preview}\n\n"
                "请根据用户要求输出可执行动作列表，支持 format/insert/delete/replace/extract/structure。\n"
                "输出格式示例：\n"
                '{{"actions": [{{"operation": "format", "target_paragraph_index": 0, "bold": true, "font_size": 16, "alignment": "center", "color_hex": null}}]}}\n'
                "字段说明：\n"
                "- operation: format/insert/delete/replace/extract/structure\n"
                "- target_paragraph_index: 段落索引（从0开始），-1 表示全文\n"
                "- target_text: 删除、替换、结构操作的目标文本或目标类型\n"
                "- content: 插入内容、替换内容、标题/页眉内容\n"
                "- bold: true/false/null\n"
                "- font_size: 整数字号或 null\n"
                "- alignment: 'left'/'center'/'right' 或 null\n"
                "- color_hex: 十六进制颜色如 '#FF0000' 或 null\n"
                "不需要修改的字段填 null，必须至少返回一个 action。"
            )),
            ("human", "用户要求：{command}"),
        ])

        plan = None
        warnings: list[str] = []
        try:
            structured_llm = get_chat_llm().with_structured_output(FormatPlan)
            plan = (prompt | structured_llm).invoke({
                "preview": preview_text,
                "command": input_data.natural_language_cmd,
            })
        except Exception as exc:
            warnings.append(f"LLM plan generation failed; used rule-based fallback: {exc}")
            plan = None
        if plan is None:
            plan = rule_plan
        elif rule_plan.actions:
            # Keep deterministic actions as a safety net for multi-intent commands.
            existing = {(action.operation, action.target_paragraph_index, action.target_text, action.content) for action in plan.actions}
            for action in rule_plan.actions:
                key = (action.operation, action.target_paragraph_index, action.target_text, action.content)
                if key not in existing:
                    plan.actions.append(action)
        if not plan.actions:
            return output_schema(status="failed", message="AI 未能生成任何格式修改动作，请尝试更具体的指令")

        action_summaries = []
        action_reports = []
        for action in plan.actions:
            operation, changed, extra = _execute_action(doc, action)
            action_summaries.append(f"{operation}:{changed}")
            action_reports.append({
                "operation": operation,
                "affected_count": changed,
                "target_paragraph_index": action.target_paragraph_index,
                "target_text": action.target_text,
                "content_preview": (action.content or "")[:120],
                **extra,
            })

        missed_actions = _unresolved_action_reports(action_reports)
        if missed_actions:
            missed_operations = "、".join(str(report["operation"]) for report in missed_actions)
            return output_schema(
                status="failed",
                message=f"文档操作未完整执行，未生效动作：{missed_operations}。请调整指令后重试。",
            )

        output_path = doc_path.parent / f"{doc_path.stem}_formatted{doc_path.suffix}"
        doc.save(output_path)
        audit_path = _write_operation_audit(
            doc_path,
            output_path,
            input_data.natural_language_cmd,
            plan.actions,
            action_reports,
            warnings,
        )
        warning_text = f"；警告：{'；'.join(warnings)}" if warnings else ""
        return output_schema(
            status="success",
            processed_file_path=str(output_path),
            message=f"文档智能操作完成，动作统计：{', '.join(action_summaries)}；审计报告：{audit_path}{warning_text}",
        )

    except Exception:
        logger.exception("Document operation failed for %s", input_data.file_path)
        return output_schema(status="failed", message="文档操作失败，请查看服务端日志。")
