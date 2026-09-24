import pytest
from fastapi.testclient import TestClient


def scenario_payload(
    scenario_id: str = "credential-basic-001",
) -> dict[str, str]:
    return {
        "scenario_id": scenario_id,
        "name": "Fictional Login Training",
        "scenario_type": "credential",
        "description": "A fictional local login exercise.",
    }


def test_create_and_get_scenario(client: TestClient) -> None:
    create_response = client.post(
        "/api/scenarios",
        json=scenario_payload(),
    )

    assert create_response.status_code == 201

    created = create_response.json()

    assert created["scenario_id"] == "credential-basic-001"
    assert created["name"] == "Fictional Login Training"
    assert created["scenario_type"] == "credential"
    assert created["description"] == "A fictional local login exercise."
    assert created["created_at"]

    get_response = client.get("/api/scenarios/credential-basic-001")

    assert get_response.status_code == 200
    assert get_response.json() == created


def test_list_scenarios_handles_empty_state(client: TestClient) -> None:
    response = client.get("/api/scenarios")

    assert response.status_code == 200
    assert response.json() == []


def test_create_scenario_rejects_duplicate_id(client: TestClient) -> None:
    payload = scenario_payload()

    first_response = client.post("/api/scenarios", json=payload)
    second_response = client.post("/api/scenarios", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Scenario with this scenario_id already exists."
    }


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {
            "scenario_id": "",
            "name": "Example",
            "scenario_type": "credential",
        },
        {
            **scenario_payload(),
            "unexpected": "value",
        },
    ],
)
def test_create_scenario_rejects_invalid_input(
    client: TestClient,
    payload: dict[str, str],
) -> None:
    response = client.post("/api/scenarios", json=payload)

    assert response.status_code == 422


def test_get_scenario_returns_not_found(client: TestClient) -> None:
    response = client.get("/api/scenarios/missing-scenario")

    assert response.status_code == 404
    assert response.json() == {"detail": "Scenario not found."}
