from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace

from docnexus.api.dependencies import require_admin
from docnexus.core.settings import Settings
from fastapi import HTTPException


def _settings(
    *,
    app_env: str = "development",
    secret_key: str | None = None,
    session_cookie_secure: bool | None = None,
) -> Settings:
    return Settings(
        app_env=app_env,
        secret_key=secret_key,
        access_token_expire_minutes=180,
        bootstrap_admin_username=None,
        bootstrap_admin_email=None,
        bootstrap_admin_password=None,
        cors_origins=("http://localhost:5173",),
        database_url="sqlite:///./doc_system.db",
        session_cookie_secure=session_cookie_secure,
    )


class SettingsSecurityTests(unittest.TestCase):
    def test_missing_secret_is_rejected(self) -> None:
        with self.assertRaises(RuntimeError):
            _settings().require_secret_key()

    def test_short_production_secret_is_rejected(self) -> None:
        with self.assertRaises(RuntimeError):
            _settings(app_env="production", secret_key="too-short").require_secret_key()

    def test_long_production_secret_is_accepted(self) -> None:
        secret = "x" * 32
        self.assertEqual(_settings(app_env="production", secret_key=secret).require_secret_key(), secret)

    def test_session_cookie_is_secure_by_default_in_production(self) -> None:
        self.assertTrue(_settings(app_env="production").secure_session_cookie)

    def test_session_cookie_can_be_disabled_for_http_ip_deployment(self) -> None:
        settings = _settings(app_env="production", session_cookie_secure=False)
        self.assertFalse(settings.secure_session_cookie)


class AdminDependencyTests(unittest.TestCase):
    def test_regular_user_is_rejected(self) -> None:
        with self.assertRaises(HTTPException) as context:
            asyncio.run(require_admin(SimpleNamespace(role="普通用户")))
        self.assertEqual(context.exception.status_code, 403)

    def test_administrator_is_returned(self) -> None:
        user = SimpleNamespace(role="管理员")
        self.assertIs(asyncio.run(require_admin(user)), user)
