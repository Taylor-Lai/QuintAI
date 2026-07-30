"""数据库迁移链的可逆性测试。"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from docnexus.core.settings import get_settings
from sqlalchemy import create_engine, text


@pytest.fixture
def sqlite_migration_config(tmp_path: Path, monkeypatch):
    database_path = tmp_path / "migration-chain.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    get_settings.cache_clear()
    project_root = Path(__file__).resolve().parents[2]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "backend" / "alembic"))
    yield config, database_path
    get_settings.cache_clear()


def test_sqlite_migration_chain_is_reversible(sqlite_migration_config) -> None:
    """默认 SQLite 配置必须能够从空库升级、降级并再次升级。"""
    config, database_path = sqlite_migration_config

    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "20260731_0008"
    engine.dispose()

    command.downgrade(config, "base")
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "20260731_0008"
    engine.dispose()
