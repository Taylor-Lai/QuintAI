"""Regression checks for third-party dependency compatibility."""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import patch

from docnexus.ai.table_engine import parsers
from docnexus.core.security import AuthService


def test_langgraph_import_has_no_allowed_objects_deprecation_warning() -> None:
    result = subprocess.run(
        [sys.executable, "-W", "default", "-c", "import langgraph.graph"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert "default value of `allowed_objects`" not in result.stderr


def test_docling_converter_is_initialized_once_per_worker() -> None:
    parsers._get_docling_converter.cache_clear()
    converter = object()
    with patch.object(parsers, "DocumentConverter", return_value=converter) as factory:
        assert parsers._get_docling_converter() is converter
        assert parsers._get_docling_converter() is converter
    factory.assert_called_once_with()
    parsers._get_docling_converter.cache_clear()


def test_password_hash_backend_supports_real_hash_and_verify() -> None:
    password = "Local-Compatibility-2026!"

    password_hash = AuthService.get_password_hash(password)

    assert password_hash.startswith("$2")
    assert AuthService.verify_password(password, password_hash)
    assert not AuthService.verify_password("wrong-password", password_hash)
