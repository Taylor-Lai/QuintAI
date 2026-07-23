"""Centralized backend configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str
    secret_key: str | None
    access_token_expire_minutes: int
    bootstrap_admin_username: str | None
    bootstrap_admin_email: str | None
    bootstrap_admin_password: str | None
    cors_origins: tuple[str, ...]
    static_dir: Path
    database_url: str
    data_dir: Path = Path("data")
    max_upload_bytes: int = 25 * 1024 * 1024
    max_upload_files: int = 10
    max_archive_entries: int = 2000
    max_archive_uncompressed_bytes: int = 100 * 1024 * 1024
    task_timeout_seconds: int = 900
    task_max_attempts: int = 2
    rate_limit_window_seconds: int = 60
    auth_rate_limit: int = 10
    ai_rate_limit: int = 6
    redis_url: str = "redis://localhost:6379/0"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def has_bootstrap_admin(self) -> bool:
        return all(
            (
                self.bootstrap_admin_username,
                self.bootstrap_admin_email,
                self.bootstrap_admin_password,
            )
        )

    def require_secret_key(self) -> str:
        if not self.secret_key:
            raise RuntimeError(
                "SECRET_KEY is not configured. Copy .env.example to .env and set a strong value."
            )
        if self.is_production and len(self.secret_key) < 32:
            raise RuntimeError("SECRET_KEY must contain at least 32 characters in production.")
        return self.secret_key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        secret_key=os.getenv("SECRET_KEY") or None,
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "180")),
        bootstrap_admin_username=os.getenv("BOOTSTRAP_ADMIN_USERNAME") or None,
        bootstrap_admin_email=os.getenv("BOOTSTRAP_ADMIN_EMAIL") or None,
        bootstrap_admin_password=os.getenv("BOOTSTRAP_ADMIN_PASSWORD") or None,
        cors_origins=_split_csv(
            os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            )
        ),
        static_dir=Path(os.getenv("STATIC_DIR", "static")),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./doc_system.db"),
        data_dir=Path(os.getenv("DATA_DIR", "data")),
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024))),
        max_upload_files=int(os.getenv("MAX_UPLOAD_FILES", "10")),
        max_archive_entries=int(os.getenv("MAX_ARCHIVE_ENTRIES", "2000")),
        max_archive_uncompressed_bytes=int(
            os.getenv("MAX_ARCHIVE_UNCOMPRESSED_BYTES", str(100 * 1024 * 1024))
        ),
        task_timeout_seconds=int(os.getenv("TASK_TIMEOUT_SECONDS", "900")),
        task_max_attempts=int(os.getenv("TASK_MAX_ATTEMPTS", "2")),
        rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
        auth_rate_limit=int(os.getenv("AUTH_RATE_LIMIT", "10")),
        ai_rate_limit=int(os.getenv("AI_RATE_LIMIT", "6")),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    )
