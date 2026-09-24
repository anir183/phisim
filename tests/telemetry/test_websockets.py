from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from phisim.infra.sqlite.connection import Base, get_session
from phisim.main import app


@pytest.fixture
def test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    yield engine

    engine.dispose()


@pytest.fixture
def client(test_engine) -> Generator[TestClient]:
    def override_get_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_event_is_broadcast_to_websocket(
    client: TestClient,
) -> None:
    event = {
        "event_id": "event-websocket-001",
        "session_id": "session-001",
        "scenario_id": "credential-basic-001",
        "event_type": "page_viewed",
        "source": "browser",
        "metadata": {
            "page": "/scenario/credential-basic-001",
        },
    }

    with client.websocket_connect("/api/events/ws") as websocket:
        response = client.post(
            "/api/events",
            json=event,
        )

        assert response.status_code == 201

        received = websocket.receive_json()

    assert received["event_id"] == event["event_id"]
    assert received["session_id"] == event["session_id"]
    assert received["scenario_id"] == event["scenario_id"]
    assert received["event_type"] == event["event_type"]
    assert received["source"] == event["source"]
    assert received["metadata"] == event["metadata"]
    assert received["id"] > 0
    assert received["timestamp"]


def test_event_is_broadcast_to_all_websocket_clients(
    client: TestClient,
) -> None:
    event = {
        "event_id": "event-websocket-002",
        "session_id": "session-002",
        "scenario_id": "credential-basic-001",
        "event_type": "link_clicked",
        "source": "browser",
        "metadata": {
            "url": "/scenario/credential-basic-001",
        },
    }

    with (
        client.websocket_connect("/api/events/ws") as websocket_one,
        client.websocket_connect("/api/events/ws") as websocket_two,
    ):
        response = client.post(
            "/api/events",
            json=event,
        )

        assert response.status_code == 201

        received_one = websocket_one.receive_json()
        received_two = websocket_two.receive_json()

    assert received_one == received_two
    assert received_one["event_id"] == event["event_id"]
