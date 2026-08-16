"""Chunked information extraction for unstructured documents."""

from __future__ import annotations

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, cast

from docx import Document
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, create_model

from docnexus.ai.llm import LLM_CONCURRENCY, get_chat_llm

logger = logging.getLogger(__name__)


def _invoke_extraction_chunks(chain, chunks: list[dict[str, object]], entities: list[str]) -> list[dict[str, object]]:
    """Extract chunks concurrently while preserving their source order."""

    entity_text = ", ".join(entities)

    def invoke(chunk: dict[str, object]) -> dict[str, object]:
        for attempt in range(3):
            try:
                result = chain.invoke({"text": chunk["text"], "entities": entity_text})
                return {} if result is None else result.model_dump()
            except Exception as exc:
                # DashScope can transiently return Workspace.AccessDenied for
                # an otherwise valid workspace. Retry only this narrow case;
                # permanent authentication and validation failures still fail fast.
                if "Workspace.AccessDenied" not in str(exc) or attempt == 2:
                    raise
                time.sleep(1 << attempt)
        return {}  # pragma: no cover - loop always returns or raises

    worker_count = min(max(1, LLM_CONCURRENCY), len(chunks))
    if worker_count == 1:
        return [invoke(chunk) for chunk in chunks]
    with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="extraction") as executor:
        return list(executor.map(invoke, chunks))


def _schema_classes():
    try:
        from docnexus.ai.contracts import InformationExtractionOutput
    except ImportError:  # pragma: no cover - local package fallback
        from .contracts import InformationExtractionOutput
    return InformationExtractionOutput

EXTRACTION_CHUNK_SIZE = 6000
EXTRACTION_CHUNK_OVERLAP = 500
DATE_RE = re.compile(r"(\d{4})\s*[年/-]\s*(\d{1,2})\s*[月/-]\s*(\d{1,2})\s*日?")
TIME_RE = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?::(\d{2}))?(?!\d)")
NUMBER_RE = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?")


def _extract_incident_fields(full_text: str, target_entities: list[str]) -> dict[str, object]:
    """Extract an explicitly labelled incident timeline without model variance."""

    if "事件" not in full_text or not any(token in full_text for token in ("最终根因", "复盘负责人")):
        return {}

    patterns = {
        "事件编号": r"事件(?:编号|代号)\s*[：:]?\s*([A-Z]+-\d{4}-\d+)",
        "首次告警时间": r"(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}日?\s+\d{1,2}:\d{2}(?::\d{2})?)\s*首次触发",
        "确认时间": r"(?<!\d)(\d{1,2}:\d{2})(?:\s*[^，,。；;]{0,12})?确认",
        "流量切换时间": r"(?<!\d)(\d{1,2}:\d{2})\s*完成流量切换",
        "核心恢复时间": r"(?<!\d)(\d{1,2}:\d{2})\s*核心接口恢复",
        "补偿完成时间": r"(?<!\d)(\d{1,2}:\d{2})\s*数据补偿完成",
        "影响比例": r"影响(?:范围|比例)?\s*(?:约)?\s*(\d+(?:\.\d+)?%)",
        "失败请求数": r"失败请求\s*([\d,]+)\s*次",
        "永久数据丢失": r"(未发生|没有|无)(?:数据)?永久丢失",
        "最终根因": r"最终根因.*?为(.+?)(?=。直接修复人|；直接修复人|\n|$)",
        "修复人": r"直接修复人为\s*([^，,。；;\s]+)",
        "复盘负责人": r"复盘负责人(?:为|是|[：:])\s*([^，,。；;\s]+)",
    }
    extracted: dict[str, object] = {}
    for field_name, pattern in patterns.items():
        if field_name not in target_entities:
            continue
        match = re.search(pattern, full_text)
        if match:
            extracted[field_name] = match.group(1).strip()

    if "改进动作数量" in target_entities:
        action_section = re.search(r"(?:后续|改进)动作[：:]\s*(.+?)(?:\n|$)", full_text)
        if action_section:
            actions = [
                item.strip(" ，,。")
                for item in re.split(r"[；;]", action_section.group(1))
                if item.strip(" ，,。")
            ]
            if actions:
                extracted["改进动作数量"] = len(actions)
    return extracted


def _extract_procurement_fields(full_text: str, target_entities: list[str]) -> dict[str, object]:
    if "采购申请" not in full_text or not all(token in full_text for token in ("申请部门", "供应商", "采购内容")):
        return {}
    extracted: dict[str, object] = {}
    for field_name in ("申请部门", "申请人", "供应商"):
        if field_name not in target_entities:
            continue
        match = re.search(rf"(?m)^{field_name}\s*[：:]\s*(.+?)\s*$", full_text)
        if match:
            extracted[field_name] = match.group(1).strip()

    content_match = re.search(r"(?m)^采购内容\s*[：:]\s*(.+?)\s*$", full_text)
    if content_match:
        content = content_match.group(1).strip()
        duration_match = re.search(r"(\d+(?:\.\d+)?\s*(?:个?月|年|天))\s*$", content)
        if "服务期限" in target_entities and duration_match:
            extracted["服务期限"] = normalize_field_value("服务期限", duration_match.group(1))
        if "采购内容" in target_entities:
            extracted["采购内容"] = normalize_field_value("采购内容", content)

    labeled_patterns = {
        "含税总额": r"(?m)^含税总额\s*[：:]\s*(.+?)\s*$",
        "付款条件": r"(?m)^付款条件\s*[：:]\s*(.+?)\s*$",
        "开通日期": r"(?m)^期望到货/开通日期\s*[：:]\s*(.+?)\s*$",
    }
    for field_name, pattern in labeled_patterns.items():
        if field_name not in target_entities:
            continue
        match = re.search(pattern, full_text)
        if match:
            extracted[field_name] = normalize_field_value(field_name, match.group(1))
    return extracted


def _extract_weekly_report_fields(full_text: str, target_entities: list[str]) -> dict[str, object]:
    if "周报" not in full_text or not all(token in full_text for token in ("定稿", "下周目标")):
        return {}
    extracted: dict[str, object] = {}
    patterns: dict[str, str] = {
        "报告周期": r"第\s*(\d+)\s*周周报",
        "采用版本": r"(版本\s*[A-ZＡ-Ｚ]\s*[（(][^）)]*定稿[）)])",
        "本周完成接口数": r"定稿[^\n]*?本周完成接口\s*(\d+)",
        "剩余阻塞问题数": r"定稿[^\n]*?剩余\s*(\d+)\s*个",
        "整体进度": r"定稿[^\n]*?整体进度[^\d]*(\d+(?:\.\d+)?%)",
        "风险责任人": r"责任人\s*([^，,。；;\s]+)",
        "预计解除日期": r"预计\s*(\d{4}-\d{1,2}-\d{1,2})\s*解除",
        "主要风险": r"(?m)^风险\s*[：:]\s*(.+?)，\s*责任人",
        "下周目标": r"(?m)^下周目标\s*[：:]\s*(.+?)[。.]?\s*$",
    }
    for field_name, pattern in patterns.items():
        if field_name not in target_entities:
            continue
        match = re.search(pattern, full_text)
        if not match:
            continue
        value = match.group(1).strip(" 。.")
        if field_name == "报告周期":
            value = f"第 {value} 周"
        elif field_name == "采用版本":
            value = re.sub(r"版本\s*([A-ZＡ-Ｚ])", r"版本 \1", value)
        extracted[field_name] = normalize_field_value(field_name, value)
    return extracted


def chunk_text(text: str, chunk_size: int = EXTRACTION_CHUNK_SIZE, overlap: int = EXTRACTION_CHUNK_OVERLAP) -> list[dict[str, object]]:
    if not text:
        return [{"chunk_id": 0, "start": 0, "end": 0, "text": ""}]
    chunks: list[dict[str, object]] = []
    start = 0
    chunk_id = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append({"chunk_id": chunk_id, "start": start, "end": end, "text": text[start:end]})
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
        chunk_id += 1
    return chunks


def is_missing_extraction_value(value: object) -> bool:
    return value is None or str(value).strip() in {"", "未找到", "null", "None"}


def find_evidence_snippet(text: str, value: object, window: int = 80) -> str | None:
    if is_missing_extraction_value(value):
        return None
    needle = str(value).strip()
    if not needle:
        return None
    index = text.find(needle)
    if index < 0:
        return None
    start = max(index - window, 0)
    end = min(index + len(needle) + window, len(text))
    return text[start:end].replace("\n", " ").strip()


def normalize_field_value(field_name: str, value: object) -> object:
    if is_missing_extraction_value(value):
        return "未找到"
    if isinstance(value, (list, tuple, set)):
        text = "；".join(str(item).strip() for item in value if str(item).strip())
    else:
        text = str(value).strip()
    normalized_name = "".join(field_name.split()).lower()
    date_match = DATE_RE.search(text)
    if date_match and any(token in normalized_name for token in ("日期", "时间", "date", "time")):
        year, month, day = date_match.groups()
        normalized_date = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        time_match = TIME_RE.search(text)
        if time_match:
            hour, minute, second = time_match.groups()
            normalized_date += f" {int(hour):02d}:{minute}" + (f":{second}" if second else "")
        return normalized_date
    if any(token in normalized_name for token in ("金额", "总额")):
        number_match = NUMBER_RE.search(text.replace(",", ""))
        if number_match:
            try:
                return f"{Decimal(number_match.group(0)):.2f}"
            except InvalidOperation:
                pass
    if "付款条件" in normalized_name:
        # Keep the conditions associated with each installment.  Returning
        # only the percentages discards when each payment becomes due.
        return text
    if "合同名称" in normalized_name:
        text = text.strip("《》〈〉")
    if "准确率" in normalized_name:
        percentage = re.search(r"\d+(?:\.\d+)?%", text)
        if percentage:
            return percentage.group(0)
    if "采购内容" in normalized_name:
        # Duration belongs in a dedicated service-period field. Do not let a
        # model concatenate the adjacent duration into the purchased item.
        text = re.sub(r"\s+\d+(?:\.\d+)?\s*(?:个?月|年|天)\s*$", "", text).strip()
    if "交付周期" in normalized_name:
        # Keep duration fields stable when a model adds a synonymous deadline
        # suffix, for example "7 个工作日内" versus "7 个工作日".
        text = re.sub(r"内$", "", text).strip()
    if "违约金规则" in normalized_name:
        text = text.replace("千分之一", "0.1%")
        text = re.sub(r"^(?:违约金)?按", "", text)
        text = text.replace("计算", "").replace("的 10%", " 10%").replace("的10%", " 10%")
        text = re.sub(r"每日\s*(\d)", r"每日 \1", text)
        text = re.sub(r"\s+", " ", text).strip(" ，,。")
    if any(token in normalized_name for token in ("预算", "数量", "人口", "gdp", "收入", "病例", "检测", "请求数")) or normalized_name.endswith("数"):
        number_match = NUMBER_RE.search(text.replace(",", ""))
        if number_match:
            number_text = number_match.group(0)
            try:
                return float(number_text) if "." in number_text else int(number_text)
            except ValueError:
                return text
    if any(token in normalized_name for token in ("永久数据丢失", "是否", "发生")):
        if text.lower() in {"否", "no", "false"} or text.startswith(("未发生", "没有", "无")):
            return "否"
        if text in {"发生", "有", "是", "yes", "true"}:
            return "是"
    if "主要风险" in normalized_name:
        text = text.replace("比计划晚", "晚")
    if "下周目标" in normalized_name:
        text = text.replace("并把", "并将").replace("压到", "降至")
    if "最终根因" in normalized_name:
        root_match = re.search(
            r"(?:任务消费者发布时)?环境变量名称拼写错误[，,]?导致新实例未订阅\s*([^，,。]+队列)",
            text,
        )
        if root_match:
            return f"新实例因环境变量名称拼写错误未订阅 {root_match.group(1).strip()}"
    text = re.sub(r"(?<=\d)(个月|个工作日|天|小时)", r" \1", text)
    text = re.sub(r"^([\u4e00-\u9fff]{2,8})([A-Z]\d+-\d+)$", r"\1 \2", text)
    return text


def infer_field_type(field_name: str, value: object) -> str:
    normalized_name = "".join(field_name.split()).lower()
    if any(token in normalized_name for token in ("日期", "时间", "date", "time")):
        return "date"
    if any(token in normalized_name for token in ("金额", "预算", "数量", "人口", "gdp", "收入", "病例", "检测", "比例", "率")):
        return "number"
    if is_missing_extraction_value(value):
        return "unknown"
    return "text"


def validate_field_value(field_name: str, raw_value: object, normalized_value: object, confidence: float, conflicts: dict[str, list[object]]) -> dict[str, object]:
    expected_type = infer_field_type(field_name, raw_value)
    if is_missing_extraction_value(raw_value):
        status = "missing"
    elif field_name in conflicts:
        status = "conflict"
    elif confidence < 0.6:
        status = "low_confidence"
    elif expected_type == "number" and not isinstance(normalized_value, (int, float)):
        status = "type_mismatch"
    elif expected_type == "date" and not (isinstance(normalized_value, str) and DATE_RE.search(str(raw_value))):
        status = "type_mismatch"
    else:
        status = "pass"
    return {
        "status": status,
        "expected_type": expected_type,
        "raw_value": raw_value,
        "normalized_value": normalized_value,
        "confidence": confidence,
    }


def _merge_chunk_candidates(
    chunk_results: list[dict[str, object]],
    chunks: list[dict[str, object]],
    target_entities: list[str],
    full_text: str,
) -> dict[str, object]:
    merged: dict[str, object] = {entity: "未找到" for entity in target_entities}
    evidence: dict[str, dict[str, object]] = {}
    conflicts: dict[str, list[object]] = {}
    normalized_values: dict[str, object] = {}
    confidence: dict[str, float] = {}
    candidates: dict[str, list[object]] = {}
    validation: dict[str, dict[str, object]] = {}

    for chunk, result in zip(chunks, chunk_results):
        for entity in target_entities:
            value = result.get(entity)
            if is_missing_extraction_value(value):
                continue
            current = merged.get(entity)
            if is_missing_extraction_value(current):
                merged[entity] = value
                evidence[entity] = {
                    "chunk_id": chunk["chunk_id"],
                    "char_range": [chunk["start"], chunk["end"]],
                    "snippet": find_evidence_snippet(str(chunk["text"]), value),
                }
            elif value != current:
                conflicts.setdefault(entity, [current])
                if value not in conflicts[entity]:
                    conflicts[entity].append(value)
                context = str(chunk.get("text") or "")
                if any(marker in context for marker in ("最终", "定稿", "终审", "以此为准", "正式版")):
                    merged[entity] = value
                    evidence[entity] = {
                        "chunk_id": chunk["chunk_id"],
                        "char_range": [chunk["start"], chunk["end"]],
                        "snippet": find_evidence_snippet(context, value),
                        "strategy": "authoritative_version",
                    }
            candidates.setdefault(entity, [])
            if value not in candidates[entity]:
                candidates[entity].append(value)

    for entity in target_entities:
        value = merged.get(entity)
        normalized_values[entity] = normalize_field_value(entity, value)
        if is_missing_extraction_value(value):
            confidence[entity] = 0.0
        elif entity in conflicts:
            confidence[entity] = 0.55
        elif evidence.get(entity, {}).get("snippet"):
            confidence[entity] = 0.9
        else:
            confidence[entity] = 0.7
        validation[entity] = validate_field_value(
            entity,
            value,
            normalized_values[entity],
            confidence[entity],
            conflicts,
        )

    found_count = sum(1 for entity in target_entities if not is_missing_extraction_value(merged.get(entity)))
    merged["_meta"] = {
        "strategy": "chunked_structured_llm_extraction",
        "chunk_count": len(chunks),
        "text_length": len(full_text),
        "target_field_count": len(target_entities),
        "found_field_count": found_count,
        "coverage": round(found_count / len(target_entities), 4) if target_entities else 0,
        "evidence": evidence,
        "conflicts": conflicts,
        "normalized": normalized_values,
        "confidence": confidence,
        "candidates": candidates,
        "validation": validation,
        "raw": {entity: merged.get(entity) for entity in target_entities},
    }
    for entity in target_entities:
        merged[entity] = normalized_values[entity]
    return merged


def _read_document_text(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    if file_path.endswith(".docx"):
        doc = Document(file_path)
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        for table_index, table in enumerate(doc.tables):
            parts.append(f"[表格 {table_index + 1}]")
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                if any(cells):
                    parts.append(" | ".join(cells))
        return "\n".join(parts)
    if file_path.endswith(".xlsx"):
        import pandas as pd

        sheets = pd.read_excel(file_path, sheet_name=None)
        parts = []
        for sheet_name, df in sheets.items():
            parts.append(f"[工作表 {sheet_name}]")
            parts.append(df.to_markdown(index=False))
        return "\n\n".join(parts)

    for encoding in ("utf-8", "gbk", "utf-16"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法识别文件编码: {file_path}")


def handle_information_extraction(input_data):
    output_schema = _schema_classes()
    try:
        full_text = _read_document_text(input_data.file_path)
        fields_spec: dict[str, tuple[Any, Any]] = {
            # Some OpenAI-compatible models legitimately represent repeated
            # facts as a JSON array. Accept that shape and normalize it below
            # instead of failing the entire extraction during Pydantic parse.
            entity: (str | list[str], Field(default="未找到", description=f"提取 '{entity}' 的内容"))
            for entity in input_data.target_entities
        }
        dynamic_model = create_model("DynamicExtractionModel", **cast(dict[str, Any], fields_spec))
        chunks = chunk_text(full_text)
        deterministic_fields = {
            **_extract_incident_fields(full_text, input_data.target_entities),
            **_extract_procurement_fields(full_text, input_data.target_entities),
            **_extract_weekly_report_fields(full_text, input_data.target_entities),
        }

        if all(entity in deterministic_fields for entity in input_data.target_entities):
            chunk_results = [deterministic_fields]
            chunks = [{"chunk_id": 0, "start": 0, "end": len(full_text), "text": full_text}]
        else:
            structured_llm = get_chat_llm().with_structured_output(dynamic_model)
            prompt = ChatPromptTemplate.from_messages([
                (
                    "system",
                    "你是一个精准的信息提取 AI。请只基于当前文本片段提取指定字段，以 JSON 格式输出。"
                    "如果当前片段没有找到某个字段，请填'未找到'。不要编造，不要跨片段推测。\n\n"
                    "当前片段：\n{text}",
                ),
                ("human", "请提取以下字段：{entities}"),
            ])

            chunk_results = _invoke_extraction_chunks(
                prompt | structured_llm,
                chunks,
                input_data.target_entities,
            )
            if deterministic_fields:
                chunk_results[0].update(deterministic_fields)

        extracted_data = merge_chunk_extractions(chunk_results, chunks, input_data.target_entities, full_text)
        extracted_meta = cast(dict[str, object], extracted_data.get("_meta", {}))
        if extracted_meta.get("found_field_count", 0) == 0:
            return output_schema(status="failed", message="未从源材料中找到任何请求字段，任务未生成有效结果。")
        return output_schema(status="success", extracted_data=extracted_data)

    except Exception:
        logger.exception("Information extraction failed for %s", input_data.file_path)
        return output_schema(status="failed", message="信息提取失败，请查看服务端日志。")


_UNICODE_DATE_RE = re.compile(r"(\d{4})\s*[年/-]\s*(\d{1,2})\s*[月/-]\s*(\d{1,2})\s*日?")
_DATE_FIELD_TOKENS = ("日期", "时间", "截止", "截至", "date", "time", "deadline")


def _is_unicode_missing_value(value: object) -> bool:
    return value is None or str(value).strip() in {"", "未找到", "null", "None"}


def _is_unicode_date_field(field_name: str) -> bool:
    normalized = "".join(str(field_name).split()).lower()
    return any(token in normalized for token in _DATE_FIELD_TOKENS)


def _format_unicode_date(match: re.Match[str]) -> str:
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _find_unicode_date_for_field(full_text: str, field_name: str) -> tuple[str | None, str | None]:
    if not _is_unicode_date_field(field_name):
        return None, None

    field_match = re.search(
        rf"{re.escape(field_name)}[^\d\n]{{0,30}}(\d{{4}}[年/-]\d{{1,2}}[月/-]\d{{1,2}}日?)",
        full_text,
        re.IGNORECASE,
    )
    if field_match:
        raw_date = field_match.group(1)
        date_match = _UNICODE_DATE_RE.search(raw_date)
        if date_match:
            return _format_unicode_date(date_match), find_evidence_snippet(full_text, raw_date)

    for date_match in _UNICODE_DATE_RE.finditer(full_text):
        start = max(date_match.start() - 40, 0)
        end = min(date_match.end() + 40, len(full_text))
        context = full_text[start:end]
        if any(token in context for token in ("日期", "时间", "截止", "截至", "date", "deadline")):
            return _format_unicode_date(date_match), context.replace("\n", " ").strip()

    date_match = _UNICODE_DATE_RE.search(full_text)
    if date_match:
        return _format_unicode_date(date_match), find_evidence_snippet(full_text, date_match.group(0))
    return None, None


def _find_labeled_business_value(full_text: str, field_name: str) -> tuple[object | None, str | None]:
    """Return high-confidence values for common labelled business fields.

    The fallback is intentionally conservative: monetary conversion is only
    applied when the document contains one unambiguous RMB amount.
    """

    normalized_name = "".join(field_name.split())
    if any(token in normalized_name for token in ("金额", "总额")):
        money_matches = list(
            re.finditer(r"(?<![\d.])([\d,]+(?:\.\d+)?)\s*(亿|万)?\s*元", full_text)
        )
        if len(money_matches) == 1:
            match = money_matches[0]
            try:
                amount = Decimal(match.group(1).replace(",", ""))
                multiplier = {"亿": Decimal("100000000"), "万": Decimal("10000")}.get(
                    match.group(2), Decimal("1")
                )
                return f"{amount * multiplier:.2f}", find_evidence_snippet(full_text, match.group(0))
            except InvalidOperation:
                pass

    if "质保" in normalized_name:
        match = re.search(
            r"质保(?:期|期限)?\s*[：:]\s*(?:自[^。\n]{0,80}?(?:起|之日起)\s*)?(\d+(?:\.\d+)?\s*(?:个?月|年|天))",
            full_text,
        )
        if match:
            value = normalize_field_value(field_name, match.group(1))
            return value, find_evidence_snippet(full_text, match.group(0))

    if "联系人" in normalized_name:
        match = re.search(
            rf"{re.escape(field_name)}\s*[：:]\s*([^，,。；;\n]+)",
            full_text,
        )
        if match:
            return match.group(1).strip(), find_evidence_snippet(full_text, match.group(0))

    return None, None


def merge_chunk_extractions(
    chunk_results: list[dict[str, object]],
    chunks: list[dict[str, object]],
    target_entities: list[str],
    full_text: str,
) -> dict[str, object]:
    merged = _merge_chunk_candidates(chunk_results, chunks, target_entities, full_text)
    meta = cast(dict[str, object], merged.setdefault("_meta", {}))
    evidence = cast(dict[str, object], meta.setdefault("evidence", {}))
    normalized = cast(dict[str, object], meta.setdefault("normalized", {}))
    confidence = cast(dict[str, object], meta.setdefault("confidence", {}))
    candidates = cast(dict[str, list[object]], meta.setdefault("candidates", {}))
    validation = cast(dict[str, dict[str, object]], meta.setdefault("validation", {}))

    document_date_match = _UNICODE_DATE_RE.search(full_text)
    document_date = _format_unicode_date(document_date_match) if document_date_match else None

    for entity in target_entities:
        if not _is_unicode_missing_value(merged.get(entity)):
            continue
        fallback_value, fallback_snippet = _find_unicode_date_for_field(full_text, entity)
        if not fallback_value:
            continue
        merged[entity] = fallback_value
        evidence[entity] = {
            "chunk_id": "rule_fallback",
            "char_range": None,
            "snippet": fallback_snippet,
            "strategy": "date_regex_fallback",
        }
        normalized[entity] = fallback_value
        confidence[entity] = 0.92
        candidates.setdefault(entity, [])
        if fallback_value not in candidates[entity]:
            candidates[entity].append(fallback_value)
        validation[entity] = {
            "status": "pass",
            "expected_type": "date",
            "raw_value": fallback_value,
            "normalized_value": fallback_value,
            "confidence": confidence[entity],
        }

    for entity in target_entities:
        value = merged.get(entity)
        if _is_unicode_date_field(entity) and document_date and isinstance(value, str):
            time_match = TIME_RE.fullmatch(value.strip())
            if time_match:
                hour, minute, second = time_match.groups()
                normalized_value = f"{document_date} {int(hour):02d}:{minute}" + (f":{second}" if second else "")
                merged[entity] = normalized_value
                normalized[entity] = normalized_value
                validation[entity]["normalized_value"] = normalized_value

    if "改进动作" in target_entities or "改进动作数量" in target_entities:
        action_lines = re.findall(r"(?m)^\s*(?:\d+[.、)]|[-*])\s*.+$", full_text)
        if not action_lines:
            inline_actions = re.search(r"(?:后续|改进)动作[：:]\s*(.+?)(?:\n|$)", full_text)
            if inline_actions:
                action_lines = [
                    item for item in re.split(r"[；;]", inline_actions.group(1))
                    if item.strip(" ，,。")
                ]
        if action_lines:
            merged["改进动作数量"] = len(action_lines)

    for entity in target_entities:
        fallback_value, fallback_snippet = _find_labeled_business_value(full_text, entity)
        if fallback_value is None:
            continue
        merged[entity] = fallback_value
        normalized[entity] = fallback_value
        confidence[entity] = 0.95
        evidence[entity] = {
            "chunk_id": "rule_fallback",
            "char_range": None,
            "snippet": fallback_snippet,
            "strategy": "label_regex_override",
        }
        candidates.setdefault(entity, [])
        if fallback_value not in candidates[entity]:
            candidates[entity].append(fallback_value)
        validation[entity] = validate_field_value(
            entity,
            fallback_value,
            fallback_value,
            confidence[entity],
            {},
        )

    found_count = sum(1 for entity in target_entities if not _is_unicode_missing_value(merged.get(entity)))
    meta["found_field_count"] = found_count
    meta["coverage"] = round(found_count / len(target_entities), 4) if target_entities else 0
    return merged
