"""Deterministic validation for extracted review fields."""

from __future__ import annotations

import re
from typing import Any


def build_review_fields(extracted_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert extraction output into user-facing review fields.

    Extraction engines may attach internal quality information under ``_meta``.
    That data enriches the review fields but must never appear as a business field.
    """
    metadata = extracted_data.get("_meta")
    metadata = metadata if isinstance(metadata, dict) else {}
    confidences = metadata.get("confidence")
    confidences = confidences if isinstance(confidences, dict) else {}
    evidence_map = metadata.get("evidence")
    evidence_map = evidence_map if isinstance(evidence_map, dict) else {}

    fields: list[dict[str, Any]] = []
    for name, raw_value in extracted_data.items():
        if str(name).startswith("_"):
            continue
        field_evidence = evidence_map.get(name)
        field_evidence = field_evidence if isinstance(field_evidence, dict) else {}
        if isinstance(raw_value, dict) and "value" in raw_value:
            value = raw_value.get("value")
            confidence = float(raw_value.get("confidence", confidences.get(name, 0.5)) or 0.5)
            evidence = str(raw_value.get("evidence") or field_evidence.get("snippet") or "")
            source_page = raw_value.get("source_page")
        else:
            value = raw_value
            confidence = float(confidences.get(name, 0.5) or 0.5)
            evidence = str(field_evidence.get("snippet") or "")
            source_page = field_evidence.get("source_page")
        fields.append({
            "name": str(name),
            "value": value,
            "confidence": max(0.0, min(confidence, 1.0)),
            "evidence": evidence,
            "source_page": source_page,
            "corrected": False,
        })
    return fields


def validate_fields(fields: list[dict[str, Any]], rules: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Return field-level issues without relying on a language model."""
    issues: list[dict[str, Any]] = []
    values = {str(field.get("name", "")): field.get("value") for field in fields}

    for field in fields:
        name = str(field.get("name", ""))
        value = field.get("value")
        confidence = float(field.get("confidence", 0.5) or 0)
        if value in (None, "", []):
            issues.append({"field": name, "level": "error", "code": "EMPTY_VALUE", "message": "字段内容为空"})
        if confidence < 0.65:
            issues.append({"field": name, "level": "warning", "code": "LOW_CONFIDENCE", "message": "识别置信度较低，建议人工核对"})
        if not str(field.get("evidence", "")).strip():
            issues.append({"field": name, "level": "warning", "code": "NO_EVIDENCE", "message": "缺少可追溯的原文证据"})

    for rule in rules or []:
        field_name = str(rule.get("field", ""))
        value = values.get(field_name)
        rule_type = rule.get("type")
        message = str(rule.get("message") or "未通过业务规则校验")
        failed = False
        if rule_type == "required":
            failed = value in (None, "", [])
        elif rule_type == "regex" and value not in (None, ""):
            try:
                failed = re.fullmatch(str(rule.get("pattern", "")), str(value)) is None
            except re.error:
                failed = True
                message = "规则中的正则表达式无效"
        elif rule_type == "min" and value not in (None, ""):
            try:
                failed = float(value) < float(rule.get("value"))
            except (TypeError, ValueError):
                failed = True
        elif rule_type == "max" and value not in (None, ""):
            try:
                failed = float(value) > float(rule.get("value"))
            except (TypeError, ValueError):
                failed = True
        if failed:
            issues.append({"field": field_name, "level": str(rule.get("level", "error")), "code": f"RULE_{str(rule_type).upper()}", "message": message})
    return issues
