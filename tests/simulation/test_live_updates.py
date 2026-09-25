from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.repos.simulation_attack import (
    SimulationAttackRepository,
)


def _launch(client: TestClient, scenario_id: str = "email-phish-001") -> dict:
    response = client.post(
        "/api/lab/launch",
        json={
            "scenario_id": scenario_id,
            "target_role": "student",
            "delay_profile": "short",
        },
    )
    assert response.status_code == 200
    return response.json()


def _make_due(engine: Engine, attack_id: str) -> None:
    with Session(engine) as database_session:
        repository = SimulationAttackRepository(database_session)
        attack = repository.get_by_attack_id(attack_id)
        assert attack is not None
        attack.delivery_due_at = datetime.now(UTC) - timedelta(seconds=1)
        repository.save(attack)


def test_dashboard_endpoint_refreshes_delivery_before_returning_state(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client)
    _make_due(test_engine, launch["attack_id"])

    response = client.get("/api/lab/dashboard")

    assert response.status_code == 200
    payload = response.json()
    attack = next(
        item
        for item in payload["attacks"]
        if item["attack_id"] == launch["attack_id"]
    )
    assert attack["status"] == "DELIVERED"
    assert attack["event_count"] is None
    assert payload["sessions"]
    assert launch["session_id"] in {
        session["session_id"] for session in payload["sessions"]
    }

    lab = client.get("/lab")
    assert "DELIVERED" in lab.text
    assert launch["attack_id"][:10] in lab.text


def test_victim_refresh_uses_current_query_and_primary_quickchat_selector(
    client: TestClient,
) -> None:
    script = client.get("/static/victim.js")

    assert script.status_code == 200
    assert "requestPath = `${path}${window.location.search}`" in script.text
    assert '".quickchat-thread-list"' in script.text
    assert "pollInFlight" in script.text
    assert "visibilitychange" in script.text
    assert 'cache: "no-store"' in script.text


def test_console_refreshes_selected_session_when_websocket_is_silent(
    client: TestClient,
) -> None:
    script = client.get("/static/console.js")

    assert script.status_code == 200
    assert "sessionsRefreshInFlight" in script.text
    assert "shouldRefreshSelection || previousSelection" in script.text
    assert 'cache: "no-store"' in script.text
