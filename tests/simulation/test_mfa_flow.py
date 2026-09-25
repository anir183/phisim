from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.models.event import Event
from phisim.infra.sqlite.repos.event import EventRepository

SCENARIO_ID = "mfa-fatigue-001"
PROMPT_COUNT = 3


def _list_events(engine: Engine, session_id: str) -> list[Event]:
    with Session(engine) as session:
        repository = EventRepository(session)
        return repository.list_by_session(session_id)


def test_prompt_page_renders_and_emits_displayed(
    client: TestClient,
    test_engine: Engine,
) -> None:
    response = client.get(f"/mfa/{SCENARIO_ID}/1")

    assert response.status_code == 200
    assert "New sign-in approval" in response.text
    assert "Step 1 of 3" in response.text

    session_id = response.cookies.get("phisim_session")
    assert session_id

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == ["mfa_prompt_displayed"]
    assert events[0].scenario_id == SCENARIO_ID
    assert events[0].metadata_["channel"] == "mfa"
    assert events[0].metadata_["step"] == 1
    assert events[0].metadata_["total_steps"] == PROMPT_COUNT
    assert events[0].metadata_["content"]
    assert events[0].metadata_["request_confirmation"] is True


def test_approving_prompts_models_fatigue(
    client: TestClient,
    test_engine: Engine,
) -> None:
    opened = client.get(f"/mfa/{SCENARIO_ID}/1")
    session_id = opened.cookies.get("phisim_session")
    assert session_id

    for step in (1, 2):
        response = client.post(
            f"/mfa/{SCENARIO_ID}/{step}",
            data={"action": "approve"},
        )
        assert response.status_code == 200
        assert response.history
        assert response.history[0].status_code == 302
        assert (
            response.history[0]
            .headers["location"]
            .startswith(f"http://testserver/mfa/{SCENARIO_ID}/{step + 1}")
        )
        assert "delay=short" in response.history[0].headers["location"]

    final = client.post(
        f"/mfa/{SCENARIO_ID}/{PROMPT_COUNT}",
        data={"action": "approve"},
    )
    assert final.status_code == 200
    assert "Sign-in decision saved" in final.text
    assert "MFA fatigue" not in final.text

    completed = client.post(f"/mfa/{SCENARIO_ID}/end")
    assert completed.status_code == 200
    assert "MFA practice outcome" in completed.text
    assert "MFA fatigue" in completed.text

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == [
        "mfa_prompt_displayed",
        "mfa_prompt_responded",
        "mfa_prompt_displayed",
        "mfa_prompt_responded",
        "mfa_prompt_displayed",
        "mfa_prompt_responded",
        "destination_reached",
        "attack_completed",
        "scenario_completed",
    ]
    response_event = next(
        event
        for event in reversed(events)
        if event.event_type == "mfa_prompt_responded"
    )
    assert response_event.metadata_["channel"] == "mfa"
    assert response_event.metadata_["step"] == PROMPT_COUNT
    assert response_event.metadata_["action"] == "approve"
    assert response_event.metadata_["mfa_fatigue"] is True
    assert response_event.metadata_["content"]
    assert all(event.session_id == session_id for event in events)


def test_denying_prompt_stops_flow(
    client: TestClient,
    test_engine: Engine,
) -> None:
    opened = client.get(f"/mfa/{SCENARIO_ID}/1")
    session_id = opened.cookies.get("phisim_session")
    assert session_id

    response = client.post(f"/mfa/{SCENARIO_ID}/1", data={"action": "deny"})

    assert response.status_code == 200
    assert "Sign-in decision saved" in response.text
    assert not response.history

    completed = client.post(f"/mfa/{SCENARIO_ID}/end")
    assert completed.status_code == 200
    assert "MFA practice outcome" in completed.text

    events = _list_events(test_engine, session_id)
    response_event = next(
        event
        for event in reversed(events)
        if event.event_type == "mfa_prompt_responded"
    )
    assert response_event.metadata_["channel"] == "mfa"
    assert response_event.metadata_["step"] == 1
    assert response_event.metadata_["action"] == "deny"
    assert response_event.metadata_["content"]


def test_mfa_rejects_invalid_inputs(client: TestClient) -> None:
    assert client.get(f"/mfa/{SCENARIO_ID}/0").status_code == 404
    assert (
        client.get(f"/mfa/{SCENARIO_ID}/{PROMPT_COUNT + 1}").status_code == 404
    )
    assert client.get(f"/mfa/{SCENARIO_ID}/not-a-number").status_code == 404
    assert client.get("/mfa/does-not-exist/1").status_code == 404
    assert (
        client.post(
            f"/mfa/{SCENARIO_ID}/1",
            data={"action": "maybe"},
        ).status_code
        == 400
    )
