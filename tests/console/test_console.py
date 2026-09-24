from fastapi.testclient import TestClient


def test_console_uses_safe_dom_rendering_and_api_contracts(
    client: TestClient,
) -> None:
    response = client.get("/console")

    assert response.status_code == 200
    assert "innerHTML" not in response.text
    assert "textContent" in response.text
    assert "replaceChildren" in response.text
    assert "/api/events/ws" in response.text
    assert "/api/analysis/sessions/" in response.text
    assert "Load latest session" in response.text
    assert "indicator" in response.text


def test_console_loads_latest_session_from_shared_api(
    client: TestClient,
) -> None:
    scenario = client.post(
        "/api/scenarios",
        json={
            "scenario_id": "console-scenario-001",
            "name": "Console scenario",
            "scenario_type": "website",
            "description": "Local console test.",
        },
    )
    assert scenario.status_code == 201
    session = client.post(
        "/api/sessions",
        json={
            "scenario_id": "console-scenario-001",
            "session_id": "console-session-001",
        },
    )
    assert session.status_code == 201

    response = client.get("/console")

    assert response.status_code == 200
    assert "/api/sessions" in response.text
    assert "Session ID" in response.text
