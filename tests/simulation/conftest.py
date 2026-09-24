from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import phisim.infra.sqlite.models_registry  # noqa: F401
from phisim.infra.sqlite.connection import Base, get_session
from phisim.simulation.routes import router as simulation_router
from phisim.telemetry.routes import router as telemetry_router


@pytest.fixture
def test_engine() -> Generator[Engine]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    yield engine

    engine.dispose()


@pytest.fixture
def client(test_engine: Engine) -> Generator[TestClient]:
    app = FastAPI()
    app.include_router(telemetry_router)
    app.include_router(simulation_router)

    def override_get_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
