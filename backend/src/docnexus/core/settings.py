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
    )
