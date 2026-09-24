from fastapi.testclient import TestClient


def test_create_event(client: TestClient) -> None:
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
    assert body["timestamp"] is not None


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
