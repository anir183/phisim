from fastapi.testclient import TestClient


def _create_session(client: TestClient) -> str:
    scenario = client.post(
        "/api/scenarios",
        json={
            "scenario_id": "analysis-scenario-001",
            "name": "Analysis scenario",
            "scenario_type": "website",
            "description": "A local test scenario.",
        },
    )
    assert scenario.status_code == 201

    session = client.post(
        "/api/sessions",
        json={
            "scenario_id": "analysis-scenario-001",
            "session_id": "analysis-session-001",
        },
    )
    assert session.status_code == 201
    return "analysis-session-001"


def test_session_analysis_returns_indicators_and_utc_timeline(
    client: TestClient,
) -> None:
    session_id = _create_session(client)

    opened = client.post(
        "/api/events",
        json={
            "event_id": "analysis-event-001",
            "session_id": session_id,
            "scenario_id": "analysis-scenario-001",
            "event_type": "scenario_opened",
            "source": "test",
            "metadata": {
                "channel": "website",
                "content": "Your account will be disabled today.",
                "requests_credentials": True,
            },
        },
    )
    assert opened.status_code == 201

    submitted = client.post(
        "/api/events",
        json={
            "event_id": "analysis-event-002",
            "session_id": session_id,
            "scenario_id": "analysis-scenario-001",
            "event_type": "credential_submission_attempted",
            "source": "test",
            "metadata": {
                "channel": "website",
                "interaction_result": "submitted",
                "field_presence": {
                    "username": True,
                    "password": True,
                },
            },
        },
    )
    assert submitted.status_code == 201

    response = client.get(f"/api/analysis/sessions/{session_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert {item["code"] for item in body["indicators"]} >= {
        "credential_request",
        "urgent_language",
    }
    assert [entry["event_type"] for entry in body["timeline"]] == [
        "scenario_opened",
        "credential_submission_attempted",
    ]
    assert all(entry["timestamp"].endswith("Z") for entry in body["timeline"])
    assert body["timeline"][0]["session_id"] == session_id
    assert body["timeline"][0]["scenario_id"] == "analysis-scenario-001"


def test_session_analysis_alias_and_unknown_session(
    client: TestClient,
) -> None:
    session_id = _create_session(client)

    response = client.get(f"/api/sessions/{session_id}/analysis")
    assert response.status_code == 200
    assert response.json()["session_id"] == session_id

    missing = client.get("/api/analysis/sessions/unknown-session")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Session not found."}
