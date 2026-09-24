import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.repos.simulation_run import SimulationRunRepository
from phisim.simulation.state import SimulationStateError, SimulationStateService


def test_simulation_run_state_is_persisted_and_merged(
    client: TestClient,
    test_engine: Engine,
) -> None:
    scenario = client.post(
        "/api/scenarios",
        json={
            "scenario_id": "state-scenario-001",
            "name": "State scenario",
            "scenario_type": "email",
            "description": "State test.",
        },
    )
    assert scenario.status_code == 201
    session = client.post(
        "/api/sessions",
        json={
            "scenario_id": "state-scenario-001",
            "session_id": "state-session-001",
        },
    )
    assert session.status_code == 201

    with Session(test_engine) as database_session:
        service = SimulationStateService(
            SimulationRunRepository(database_session)
        )
        run = service.get_or_create(
            session_id="state-session-001",
            scenario_id="state-scenario-001",
            channel="email",
            initial_state={"auth_stage": "landing"},
        )
        service.update(run.run_id, {"last_action": "message_opened"})
        service.update(
            run.run_id,
            {"read_message_ids": ["message-001"]},
        )
        refreshed = service.get(run.run_id)
        assert refreshed.state == {
            "auth_stage": "landing",
            "last_action": "message_opened",
            "read_message_ids": ["message-001"],
        }


def test_simulation_state_rejects_unknown_or_secret_fields(
    client: TestClient,
    test_engine: Engine,
) -> None:
    scenario = client.post(
        "/api/scenarios",
        json={
            "scenario_id": "state-scenario-002",
            "name": "State scenario",
            "scenario_type": "email",
            "description": "State test.",
        },
    )
    assert scenario.status_code == 201
    session = client.post(
        "/api/sessions",
        json={
            "scenario_id": "state-scenario-002",
            "session_id": "state-session-002",
        },
    )
    assert session.status_code == 201

    with Session(test_engine) as database_session:
        service = SimulationStateService(
            SimulationRunRepository(database_session)
        )
        run = service.get_or_create(
            session_id="state-session-002",
            scenario_id="state-scenario-002",
            channel="email",
        )
        with pytest.raises(SimulationStateError):
            service.update(run.run_id, {"username": "fictional-user"})
        with pytest.raises(SimulationStateError):
            service.update(
                run.run_id,
                {"last_action": {"password": "fictional-secret"}},
            )
