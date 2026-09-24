from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Request, Response
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.models.simulation_environment import (
    SimulationEnvironment,
)
from phisim.infra.sqlite.repos.scenario import ScenarioRepository
from phisim.infra.sqlite.repos.session import SessionRepository
from phisim.infra.sqlite.repos.simulation_environment import (
    SimulationEnvironmentRepository,
)
from phisim.scenarios.schemas import ScenarioCreate
from phisim.scenarios.service import ScenarioService
from phisim.sessions.schemas import SessionCreate
from phisim.sessions.service import SessionService

VICTIM_CONTEXT_COOKIE = "phisim_victim_context"
VICTIM_ENVIRONMENT_SCENARIO_ID = "victim-environment"
_VALID_TOKEN_LENGTH = 32


def _valid_token(value: str | None) -> bool:
    return (
        value is not None
        and len(value) == _VALID_TOKEN_LENGTH
        and all(char in "0123456789abcdef" for char in value)
    )


def get_or_create_victim_environment(
    request: Request,
    response: Response,
    database_session: OrmSession,
) -> SimulationEnvironment:
    repository = SimulationEnvironmentRepository(database_session)
    token = request.cookies.get(VICTIM_CONTEXT_COOKIE)
    if token is not None and _valid_token(token):
        environment = repository.get_by_token(token)
        if environment is not None:
            return environment

    scenario_repository = ScenarioRepository(database_session)
    if (
        scenario_repository.get_by_scenario_id(VICTIM_ENVIRONMENT_SCENARIO_ID)
        is None
    ):
        ScenarioService(scenario_repository).create(
            ScenarioCreate(
                scenario_id=VICTIM_ENVIRONMENT_SCENARIO_ID,
                name="Fictional victim environment",
                scenario_type="environment",
                description="Local baseline mailbox and messaging environment.",
            )
        )

    session_id = uuid4().hex
    SessionService(
        SessionRepository(database_session),
        scenario_repository,
    ).create(
        SessionCreate(
            scenario_id=VICTIM_ENVIRONMENT_SCENARIO_ID,
            session_id=session_id,
        )
    )
    now = datetime.now(UTC)
    environment = repository.create(
        SimulationEnvironment(
            environment_id=uuid4().hex,
            token=uuid4().hex,
            session_id=session_id,
            created_at=now,
            updated_at=now,
        )
    )
    response.set_cookie(
        VICTIM_CONTEXT_COOKIE,
        environment.token,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return environment
