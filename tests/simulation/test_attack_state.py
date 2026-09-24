from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.repos.simulation_attack import (
    SimulationAttackRepository,
)
from phisim.simulation.attack import (
    ATTACK_STATUSES,
    SimulationAttackError,
    SimulationAttackService,
)
from phisim.simulation.timing import delivery_delay_ms


def test_attack_lifecycle_and_delay_profiles_are_bounded() -> None:
    assert {
        "DRAFT",
        "ARMED",
        "LAUNCHING",
        "DELIVERED",
        "ENGAGED",
        "COMPLETED",
        "ABANDONED",
        "EXPIRED",
        "BLOCKED",
    } <= ATTACK_STATUSES
    assert delivery_delay_ms("instant") == 0
    assert delivery_delay_ms("short") == 1200
    assert delivery_delay_ms("standard") == 2400
    assert delivery_delay_ms("unknown") == 1200


def test_invalid_attack_transition_fails_closed(
    client: TestClient,
    test_engine: Engine,
) -> None:
    response = client.post(
        "/api/lab/launch",
        json={
            "scenario_id": "email-phish-001",
            "target_role": "student",
            "delay_profile": "instant",
        },
    )
    assert response.status_code == 200
    attack_id = response.json()["attack_id"]
    with Session(test_engine) as database_session:
        repository = SimulationAttackRepository(database_session)
        attack = repository.get_by_attack_id(attack_id)
        assert attack is not None
        with pytest.raises(SimulationAttackError):
            SimulationAttackService(repository).transition(attack, "COMPLETED")

        attack.delivery_due_at = datetime.now(UTC) - timedelta(seconds=1)
        repository.save(attack)
        assert SimulationAttackService(repository).deliver_if_due(attack)
        assert attack.status == "DELIVERED"


def test_operator_can_abandon_an_armed_attack(
    client: TestClient,
) -> None:
    launch = client.post(
        "/api/lab/launch",
        json={
            "scenario_id": "email-phish-001",
            "target_role": "student",
            "delay_profile": "short",
        },
    ).json()
    response = client.post(f"/api/lab/attacks/{launch['attack_id']}/abandon")

    assert response.status_code == 200
    assert response.json()["status"] == "ABANDONED"
