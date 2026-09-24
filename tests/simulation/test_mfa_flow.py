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
    assert "Approve sign-in request" in response.text
    assert "Step 1 of 3" in response.text

    session_id = response.cookies.get("phisim_session")
    assert session_id

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == ["mfa_prompt_displayed"]
    assert events[0].scenario_id == SCENARIO_ID
    assert events[0].metadata_ == {
        "channel": "website",
        "step": 1,
        "total_steps": PROMPT_COUNT,
    }


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
            .endswith(f"/mfa/{SCENARIO_ID}/{step + 1}")
        )

    final = client.post(
        f"/mfa/{SCENARIO_ID}/{PROMPT_COUNT}",
        data={"action": "approve"},
    )
    assert final.status_code == 200
    assert "Simulation Complete" in final.text
    assert "MFA fatigue" in final.text

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == [
        "mfa_prompt_displayed",
        "mfa_prompt_responded",
        "mfa_prompt_displayed",
        "mfa_prompt_responded",
        "mfa_prompt_displayed",
        "mfa_prompt_responded",
    ]
    assert events[-1].metadata_ == {
        "channel": "website",
        "step": PROMPT_COUNT,
        "action": "approve",
    }
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
    assert "You denied the prompt." in response.text
    assert not response.history

    events = _list_events(test_engine, session_id)
    assert events[-1].metadata_ == {
        "channel": "website",
        "step": 1,
        "action": "deny",
    }


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
