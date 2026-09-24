from secrets import token_hex

from fastapi import Request, Response
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.repos.scenario import ScenarioRepository
from phisim.infra.sqlite.repos.session import SessionRepository
from phisim.scenarios.schemas import ScenarioCreate
from phisim.scenarios.service import DuplicateScenarioError, ScenarioService
from phisim.sessions.schemas import SessionCreate
from phisim.sessions.service import DuplicateSessionError, SessionService

SESSION_COOKIE = "phisim_session"
_SESSION_HEX = frozenset("0123456789abcdef")


def _valid_session_id(value: str | None) -> str | None:
    if value is None or not 1 <= len(value) <= 64:
        return None
    if any(char not in _SESSION_HEX for char in value):
        return None
    return value


def _set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        httponly=True,
        samesite="lax",
        path="/",
    )


def ensure_simulation_session(
    request: Request,
    response: Response,
    database_session: OrmSession,
    *,
    scenario_id: str,
    scenario_name: str,
    scenario_type: str,
    description: str,
) -> str:
    scenario_repository = ScenarioRepository(database_session)
    if scenario_repository.get_by_scenario_id(scenario_id) is None:
        scenario_service = ScenarioService(scenario_repository)
        try:
            scenario_service.create(
                ScenarioCreate(
                    scenario_id=scenario_id,
                    name=scenario_name,
                    scenario_type=scenario_type,
                    description=description,
                )
            )
        except DuplicateScenarioError:
            pass

    session_id = _valid_session_id(request.cookies.get(SESSION_COOKIE))
    if session_id is None:
        session_id = token_hex(16)
        _set_session_cookie(response, session_id)

    session_repository = SessionRepository(database_session)
    if session_repository.get_by_session_id(session_id) is None:
        session_service = SessionService(
            session_repository,
            scenario_repository,
        )
        try:
            session_service.create(
                SessionCreate(
                    scenario_id=scenario_id,
                    session_id=session_id,
                )
            )
        except DuplicateSessionError:
            pass

    return session_id


def complete_simulation_session(
    database_session: OrmSession,
    session_id: str,
) -> None:
    session_repository = SessionRepository(database_session)
    SessionService(
        session_repository,
        ScenarioRepository(database_session),
    ).complete(session_id)
