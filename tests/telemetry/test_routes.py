import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.repos.event import EventRepository


def test_create_event_accepts_free_form_ids(client: TestClient) -> None:
    response = client.post(
        "/api/events",
        json={
            "event_id": "event-001",
            "session_id": "session-001",
            "scenario_id": "credential-basic-001",
            "event_type": "page_viewed",
            "source": "browser",
            "metadata": {
                "page": "/scenario/credential-basic-001",
            },
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] == 1
    assert body["event_id"] == "event-001"
    assert body["event_type"] == "page_viewed"
    assert body["metadata"]["page"] == ("/scenario/credential-basic-001")
    assert body["timestamp"].endswith("Z")


def test_create_event_rejects_missing_event_id(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/events",
        json={
            "session_id": "session-001",
            "scenario_id": "credential-basic-001",
            "event_type": "page_viewed",
            "source": "browser",
        },
    )

    assert response.status_code == 422


def test_create_event_rejects_empty_event_id(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/events",
        json={
            "event_id": "",
            "session_id": "session-001",
            "scenario_id": "credential-basic-001",
            "event_type": "page_viewed",
            "source": "browser",
        },
    )

    assert response.status_code == 422


def test_create_event_rejects_duplicate_event_id(
    client: TestClient,
    test_engine: Engine,
) -> None:
    event = {
        "event_id": "event-duplicate",
        "session_id": "session-001",
        "scenario_id": "credential-basic-001",
        "event_type": "page_viewed",
        "source": "browser",
        "metadata": {
            "page": "/scenario/credential-basic-001",
        },
    }

    first_response = client.post(
        "/api/events",
        json=event,
    )

    second_response = client.post(
        "/api/events",
        json=event,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Event with this event_id already exists.",
    }

    with Session(test_engine) as session:
        repository = EventRepository(session)

        assert len(repository.list_by_session("session-001")) == 1


def test_list_events_by_session(client: TestClient) -> None:
    first_event = {
        "event_id": "event-list-001",
        "session_id": "session-001",
        "scenario_id": "scenario-001",
        "event_type": "scenario_opened",
        "source": "browser",
        "metadata": {},
    }
    second_event = {
        **first_event,
        "event_id": "event-list-002",
        "event_type": "credential_submission_attempted",
        "metadata": {
            "field_presence": {
                "username": True,
                "password": True,
            }
        },
    }

    first_response = client.post("/api/events", json=first_event)
    second_response = client.post("/api/events", json=second_event)
    list_response = client.get(
        "/api/events",
        params={"session_id": "session-001"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert list_response.status_code == 200

    listed_events = list_response.json()

    assert [event["event_id"] for event in listed_events] == [
        "event-list-001",
        "event-list-002",
    ]
    assert all(event["timestamp"].endswith("Z") for event in listed_events)


def test_list_events_handles_unknown_session(client: TestClient) -> None:
    response = client.get(
        "/api/events",
        params={"session_id": "unknown-session"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_events_requires_session_id(client: TestClient) -> None:
    response = client.get("/api/events")

    assert response.status_code == 422


@pytest.mark.parametrize(
    "metadata",
    [
        {"password": "simulated-secret-value"},
        {"note": "simulated-secret-value"},
        {"details": {"password_hash": "simulated-secret-value"}},
        {"items": [{"credentials": "simulated-secret-value"}]},
        {
            "field_presence": {
                "password": "simulated-secret-value",
            }
        },
    ],
)
def test_create_event_rejects_credential_metadata_safely(
    client: TestClient,
    test_engine: Engine,
    metadata: dict[str, object],
) -> None:
    response = client.post(
        "/api/events",
        json={
            "event_id": "event-unsafe-001",
            "session_id": "session-001",
            "scenario_id": "credential-basic-001",
            "event_type": "credential_submission_attempted",
            "source": "browser",
            "metadata": metadata,
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Event metadata contains forbidden credential data."
    }
    assert "simulated-secret-value" not in response.text

    with Session(test_engine) as session:
        repository = EventRepository(session)

        assert repository.get_by_event_id("event-unsafe-001") is None


def test_create_event_validation_error_does_not_echo_metadata(
    client: TestClient,
    test_engine: Engine,
) -> None:
    response = client.post(
        "/api/events",
        json={
            "event_id": "event-invalid-metadata",
            "session_id": "session-001",
            "scenario_id": "credential-basic-001",
            "event_type": "credential_submission_attempted",
            "source": "browser",
            "metadata": "simulated-secret-value",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request payload."}
    assert "simulated-secret-value" not in response.text

    with Session(test_engine) as session:
        repository = EventRepository(session)

        assert repository.get_by_event_id("event-invalid-metadata") is None


def test_create_event_rejects_client_timestamp(
    client: TestClient,
    test_engine: Engine,
) -> None:
    response = client.post(
        "/api/events",
        json={
            "event_id": "event-client-timestamp",
            "session_id": "session-001",
            "scenario_id": "credential-basic-001",
            "event_type": "scenario_opened",
            "source": "browser",
            "timestamp": "2000-01-01T00:00:00Z",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request payload."}

    with Session(test_engine) as session:
        repository = EventRepository(session)

        assert repository.get_by_event_id("event-client-timestamp") is None


def test_create_event_allows_safe_field_presence(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/events",
        json={
            "event_id": "event-safe-001",
            "session_id": "session-001",
            "scenario_id": "credential-basic-001",
            "event_type": "credential_submission_attempted",
            "source": "browser",
            "metadata": {
                "field_presence": {
                    "username": True,
                    "password": False,
                }
            },
        },
    )

    assert response.status_code == 201
    assert response.json()["metadata"] == {
        "field_presence": {
            "username": True,
            "password": False,
        }
    }
