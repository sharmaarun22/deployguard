from pathlib import Path

import alembic.command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from backend.app.config import settings

ROOT = Path(__file__).resolve().parents[1]


def _config() -> Config:
    return Config(str(ROOT / "alembic.ini"))


def test_fresh_and_existing_sqlite_databases_upgrade_without_losing_rows(
    tmp_path: Path, monkeypatch
) -> None:
    fresh_url = f"sqlite:///{tmp_path / 'fresh.db'}"
    monkeypatch.setattr(settings, "database_url", fresh_url)
    alembic.command.upgrade(_config(), "head")
    fresh_engine = create_engine(fresh_url)
    assert "pipeline_executions" in inspect(fresh_engine).get_table_names()
    fresh_engine.dispose()

    existing_url = f"sqlite:///{tmp_path / 'existing.db'}"
    monkeypatch.setattr(settings, "database_url", existing_url)
    alembic.command.upgrade(_config(), "0001_initial")
    existing_engine = create_engine(existing_url)
    with existing_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO pipelines (name, repository, status, source, findings, created_at) "
                "VALUES ('legacy', NULL, 'unknown', 'jobs: {}', '[]', '2025-01-01 00:00:00')"
            )
        )
        connection.execute(text("DROP TABLE alembic_version"))

    alembic.command.upgrade(_config(), "head")
    with existing_engine.connect() as connection:
        assert connection.scalar(text("SELECT name FROM pipelines WHERE id = 1")) == "legacy"
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "0002_execution_history_utc"
        )
    assert "pipeline_executions" in inspect(existing_engine).get_table_names()
    assert any(
        index["name"] == "ix_pipeline_executions_pipeline_created"
        for index in inspect(existing_engine).get_indexes("pipeline_executions")
    )
    existing_engine.dispose()
