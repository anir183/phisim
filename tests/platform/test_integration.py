from fastapi.testclient import TestClient


def test_scenario_session_event_retrieval(client: TestClient) -> None:
    scenario_response = client.post(
        "/api/scenarios",
        json={
            "scenario_id": "credential-basic-001",
            "name": "Fictional Login Training",
            "scenario_type": "credential",
            "description": "A fictional local login exercise.",
        },
    )
    session_response = client.post(
        "/api/sessions",
        json={
            "scenario_id": "credential-basic-001",
            "session_id": "session-integration-001",
        },
    )
    event_response = client.post(
        "/api/events",
        json={
            "event_id": "event-integration-001",
            "session_id": "session-integration-001",
            "scenario_id": "credential-basic-001",
            "event_type": "credential_submission_attempted",
            "source": "browser",
            "metadata": {
                "field_presence": {
                    "username": True,
                    "password": True,
                }
            },
        },
    )
    events_response = client.get(
        "/api/events",
        params={"session_id": "session-integration-001"},
    )

    assert scenario_response.status_code == 201
    assert session_response.status_code == 201
    assert event_response.status_code == 201
    assert events_response.status_code == 200
    assert [event["event_id"] for event in events_response.json()] == [
        "event-integration-001"
    ]
