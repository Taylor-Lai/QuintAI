"""Competition-friendly quality summaries and safe deterministic repairs."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


def extraction_quality(fields: list[dict[str, Any]], issues: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(fields)
    populated = sum(field.get("value") not in (None, "", []) for field in fields)
    evidenced = sum(bool(str(field.get("evidence") or "").strip()) for field in fields)
    confidences = [float(field.get("confidence", 0) or 0) for field in fields]
    errors = sum(issue.get("level") == "error" for issue in issues)
    warnings = len(issues) - errors
    return {
        "kind": "extraction",
        "field_count": total,
        "completeness": round(populated / total, 4) if total else 0,
        "evidence_coverage": round(evidenced / total, 4) if total else 0,
        "average_confidence": round(sum(confidences) / len(confidences), 4) if confidences else 0,
        "errors": errors,
        "warnings": warnings,
        "requires_review": errors > 0 or warnings > 0,
    }


def table_quality(report: dict[str, Any]) -> dict[str, Any]:
    written = int(report.get("written_cell_count") or 0)
    non_empty = int(report.get("non_empty_written_cell_count") or 0)
    traceable = int(report.get("traceable_cell_count") or 0)
    checks = report.get("checks") or []
    failed = sum(check.get("status") == "fail" for check in checks if isinstance(check, dict))
    return {
        "kind": "table_fill",
        "verification_status": report.get("verification_status", "unknown"),
        "verification_summary": report.get("verification_summary", ""),
        "written_cells": written,
        "completeness": round(non_empty / written, 4) if written else 0,
        "evidence_coverage": round(traceable / max(1, non_empty), 4),
        "checks_total": len(checks),
        "checks_failed": failed,
        "warnings": len(report.get("warnings") or []),
        "requires_review": failed > 0 or report.get("verification_status") != "pass",
    }


def safely_repair_fields(fields: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Apply only lossless repairs: whitespace, thousands separators and full-width punctuation."""
    repaired = deepcopy(fields)
    changes: list[dict[str, str]] = []
    for field in repaired:
        value = field.get("value")
        if not isinstance(value, str):
            continue
        original = value
        value = re.sub(r"[ \t]+", " ", value).strip()
        value = value.replace("，", ",").replace("：", ":")
        if re.fullmatch(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?", value):
            value = value.replace(",", "")
        if value != original:
            field.setdefault("original_value", original)
            field["value"] = value
            field["corrected"] = True
            field["auto_fixed"] = True
            changes.append({"field": str(field.get("name", "")), "before": original, "after": value})
    return repaired, changes
