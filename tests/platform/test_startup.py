from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL

import phisim.infra.sqlite.connection as connection
from phisim.main import app


def test_health_endpoint_is_local_and_success() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_lifespan_initializes_temporary_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "phisim.db"
    default_database_path = tmp_path / "default-phisim.db"
    database_url = URL.create("sqlite", database=str(database_path))
    engine = create_engine(database_url)
    monkeypatch.setattr(connection, "engine", engine)
    monkeypatch.setattr(
        connection,
        "DEFAULT_DATABASE_PATH",
        default_database_path,
    )
    monkeypatch.setattr(
        connection.settings,
        "db_url",
        database_url.render_as_string(hide_password=False),
    )

    try:
        with TestClient(app):
            pass

        table_names = set(inspect(engine).get_table_names())

        assert {"events", "scenarios", "sessions"} <= table_names
        assert not default_database_path.exists()
    finally:
        engine.dispose()
