from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.models.simulation_run import SimulationRun
from phisim.infra.sqlite.repos.simulation_run import SimulationRunRepository
from phisim.simulation.emit import emit_event
from phisim.simulation.lifecycle import (
    SESSION_COOKIE,
    ensure_simulation_session,
)
from phisim.simulation.state import SimulationStateError, SimulationStateService
from phisim.simulation.timing import timing_for_request
from phisim.telemetry.service import DuplicateEventError
from phisim.utils.paths import TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


async def emit_simulation_event(
    database_session: OrmSession,
    session_id: str,
    *,
    scenario_id: str,
    event_type: str,
    metadata: dict[str, Any],
    source: str = "browser",
) -> None:
    try:
        await emit_event(
            session=database_session,
            session_id=session_id,
            scenario_id=scenario_id,
            event_type=event_type,
            source=source,
            metadata=metadata,
        )
    except DuplicateEventError:
        return


def get_or_create_run(
    database_session: OrmSession,
    *,
    session_id: str,
    scenario_id: str,
    channel: str,
    initial_state: dict[str, Any] | None = None,
) -> SimulationRun:
    return SimulationStateService(
        SimulationRunRepository(database_session)
    ).get_or_create(
        session_id=session_id,
        scenario_id=scenario_id,
        channel=channel,
        initial_state=initial_state,
    )


def get_run_state(database_session: OrmSession, run_id: str) -> dict[str, Any]:
    try:
        return (
            SimulationStateService(SimulationRunRepository(database_session))
            .get(run_id)
            .state
        )
    except SimulationStateError:
        return {}


def update_run_state(
    database_session: OrmSession,
    run_id: str,
    changes: dict[str, Any],
) -> None:
    SimulationStateService(SimulationRunRepository(database_session)).update(
        run_id,
        changes,
    )


def session_state_values(
    request: Request,
    database_session: OrmSession,
    key: str,
) -> set[str]:
    session_id = request.cookies.get(SESSION_COOKIE)
    if not session_id:
        return set()
    values: set[str] = set()
    repository = SimulationRunRepository(database_session)
    for run in repository.list_by_session(session_id):
        value = run.state.get(key, [])
        if isinstance(value, list):
            values.update(str(item) for item in value)
    return values


def redirect_to_credential_site(
    request: Request,
    database_session: OrmSession,
    *,
    scenario_id: str,
    scenario_name: str,
    scenario_type: str,
    description: str,
    target_scenario_id: str,
) -> tuple[RedirectResponse, str]:
    location = request.url_for(
        "scenario_login",
        scenario_id=target_scenario_id,
    )
    response = RedirectResponse(str(location), status_code=302)
    session_id = ensure_simulation_session(
        request,
        response,
        database_session,
        scenario_id=scenario_id,
        scenario_name=scenario_name,
        scenario_type=scenario_type,
        description=description,
    )
    return response, session_id


def timing_context(request: Request, **context: Any) -> dict[str, Any]:
    delay_profile, delay_ms = timing_for_request(request)
    return {
        **context,
        "delay_profile": delay_profile,
        "delay_ms": delay_ms,
    }
