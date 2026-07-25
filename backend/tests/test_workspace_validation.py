"""Tests for deterministic review validation."""

from docnexus.services.validation import build_review_fields, validate_fields


def test_validation_reports_empty_low_confidence_and_missing_evidence() -> None:
    issues = validate_fields([{"name": "合同金额", "value": "", "confidence": 0.4, "evidence": ""}])
    assert {item["code"] for item in issues} == {"EMPTY_VALUE", "LOW_CONFIDENCE", "NO_EVIDENCE"}


def test_validation_applies_business_rules() -> None:
    fields = [{"name": "合同金额", "value": "50", "confidence": 0.9, "evidence": "合同金额为 50 元"}]
    rules = [{"field": "合同金额", "type": "min", "value": 100, "message": "金额不能低于 100"}]
    assert validate_fields(fields, rules) == [
        {"field": "合同金额", "level": "error", "code": "RULE_MIN", "message": "金额不能低于 100"}
    ]


def test_validation_accepts_valid_field() -> None:
    fields = [{"name": "合同编号", "value": "HT-2026-01", "confidence": 0.96, "evidence": "编号 HT-2026-01"}]
    rules = [{"field": "合同编号", "type": "regex", "pattern": r"HT-\d{4}-\d{2}"}]
    assert validate_fields(fields, rules) == []


def test_review_fields_use_metadata_without_exposing_internal_field() -> None:
    extracted = {
        "报告标题": "行业报告",
        "_meta": {
            "confidence": {"报告标题": 0.92},
            "evidence": {"报告标题": {"snippet": "2026 年行业报告"}},
        },
    }
    assert build_review_fields(extracted) == [
        {
            "name": "报告标题",
            "value": "行业报告",
            "original_value": "行业报告",
            "confidence": 0.92,
            "evidence": "2026 年行业报告",
            "source_page": None,
            "corrected": False,
            "auto_fixed": False,
        }
    ]
