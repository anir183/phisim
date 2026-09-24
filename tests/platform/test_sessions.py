import pytest
from fastapi.testclient import TestClient


def create_scenario(
    client: TestClient,
    scenario_id: str = "credential-basic-001",
) -> None:
    response = client.post(
        "/api/scenarios",
        json={
            "scenario_id": scenario_id,
            "name": "Fictional Login Training",
            "scenario_type": "credential",
            "description": "A fictional local login exercise.",
        },
    )

    assert response.status_code == 201


def test_create_session_generates_session_id(client: TestClient) -> None:
    create_scenario(client)

    response = client.post(
        "/api/sessions",
        json={"scenario_id": "credential-basic-001"},
    )

    assert response.status_code == 201

    body = response.json()

    assert body["session_id"]
    assert body["scenario_id"] == "credential-basic-001"
    assert body["status"] == "active"
    assert body["started_at"].endswith("Z")
    assert body["completed_at"] is None


def test_create_session_preserves_supplied_session_id(
    client: TestClient,
) -> None:
    create_scenario(client)

    response = client.post(
        "/api/sessions",
        json={
            "scenario_id": "credential-basic-001",
            "session_id": "session-001",
        },
    )

    assert response.status_code == 201
    assert response.json()["session_id"] == "session-001"


def test_create_session_rejects_duplicate_supplied_id(
    client: TestClient,
) -> None:
    create_scenario(client)
    payload = {
        "scenario_id": "credential-basic-001",
        "session_id": "session-001",
    }

    first_response = client.post("/api/sessions", json=payload)
    second_response = client.post("/api/sessions", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Session with this session_id already exists."
    }


def test_create_session_requires_existing_scenario(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/sessions",
        json={"scenario_id": "missing-scenario"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Scenario not found."}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"scenario_id": "credential-basic-001", "session_id": ""},
        {
            "scenario_id": "credential-basic-001",
            "status": "completed",
        },
    ],
)
def test_create_session_rejects_invalid_input(
    client: TestClient,
    payload: dict[str, str],
) -> None:
    create_scenario(client)

    response = client.post("/api/sessions", json=payload)

    assert response.status_code == 422


def test_get_and_list_sessions(client: TestClient) -> None:
    empty_response = client.get("/api/sessions")
    create_scenario(client)
    create_response = client.post(
        "/api/sessions",
        json={
            "scenario_id": "credential-basic-001",
            "session_id": "session-001",
        },
    )
    get_response = client.get("/api/sessions/session-001")
    list_response = client.get("/api/sessions")

    assert empty_response.status_code == 200
    assert empty_response.json() == []
    assert create_response.status_code == 201
    assert get_response.status_code == 200
    assert get_response.json() == create_response.json()
    assert list_response.status_code == 200
    assert list_response.json() == [create_response.json()]


def test_complete_session_is_idempotent(client: TestClient) -> None:
    create_scenario(client)
    create_response = client.post(
        "/api/sessions",
        json={
            "scenario_id": "credential-basic-001",
            "session_id": "session-001",
        },
    )

    first_response = client.post("/api/sessions/session-001/complete")
    second_response = client.post("/api/sessions/session-001/complete")

    assert create_response.status_code == 201
    assert first_response.status_code == 200

    completed = first_response.json()

    assert completed["status"] == "completed"
    assert completed["completed_at"].endswith("Z")
    assert second_response.status_code == 200
    assert second_response.json() == completed


def test_session_routes_return_not_found(client: TestClient) -> None:
    get_response = client.get("/api/sessions/missing-session")
    complete_response = client.post("/api/sessions/missing-session/complete")

    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Session not found."}
    assert complete_response.status_code == 404
    assert complete_response.json() == {"detail": "Session not found."}
