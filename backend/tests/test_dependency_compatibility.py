"""Regression checks for third-party dependency compatibility."""

from __future__ import annotations

import subprocess
import sys


def test_langgraph_import_has_no_allowed_objects_deprecation_warning() -> None:
    result = subprocess.run(
        [sys.executable, "-W", "default", "-c", "import langgraph.graph"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert "default value of `allowed_objects`" not in result.stderr
