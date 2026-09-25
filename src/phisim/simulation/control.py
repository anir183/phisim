from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
)
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.connection import get_session
from phisim.infra.sqlite.repos.event import EventRepository
from phisim.infra.sqlite.repos.session import SessionRepository
from phisim.infra.sqlite.repos.simulation_attack import (
    SimulationAttackRepository,
)
from phisim.infra.sqlite.repos.simulation_run import SimulationRunRepository
from phisim.sessions.service import SessionNotFoundError
from phisim.simulation.attack import (
    SimulationAttackError,
    SimulationAttackService,
)
from phisim.simulation.catalog import (
    CatalogSummary,
    attack_types,
    catalog_summaries,
)
from phisim.simulation.emit import emit_event
from phisim.simulation.environment import get_or_create_victim_environment
from phisim.simulation.lifecycle import (
    complete_simulation_session,
    ensure_simulation_session,
)
from phisim.simulation.state import SimulationStateError, SimulationStateService
from phisim.utils.datetime import serialize_utc_datetime
from phisim.utils.paths import TEMPLATES_DIR

router = APIRouter(tags=["scenario-lab"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", include_in_schema=False)
def application_home() -> RedirectResponse:
    return RedirectResponse("/lab", status_code=307)


DelayProfile = Literal["instant", "short", "standard"]
TARGET_ROLE_CHOICES = frozenset(
    {
        "student",
        "faculty",
        "university employee",
        "billing administrator",
        "support agent",
        "online shopper",
        "collaborator",
    }
)


class LabLaunchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1, max_length=64)
    target_role: str = Field(default="student", min_length=1, max_length=64)
    delay_profile: DelayProfile = "short"


def _summary(scenario_id: str) -> CatalogSummary | None:
    return next(
        (
            summary
            for summary in catalog_summaries()
            if summary.scenario_id == scenario_id
        ),
        None,
    )


def _launch_path(summary: CatalogSummary) -> str:
    if summary.channel == "email":
        return f"/inbox/{summary.scenario_id}"
    if summary.channel == "sms":
        return f"/sms/{summary.scenario_id}"
    if summary.channel == "qr":
        return f"/qr/{summary.scenario_id}"
    if summary.channel == "mfa":
        return f"/mfa/{summary.scenario_id}/1"
    return f"/scenario/{summary.scenario_id}"


def _victim_path(channel: str, token: str, scenario_id: str) -> str:
    if channel == "email":
        return f"/v/{token}/mail"
    if channel == "sms":
        return f"/v/{token}/messages"
    if channel == "qr":
        return f"/v/{token}/qr/{scenario_id}"
    if channel == "mfa":
        return f"/v/{token}/mfa/{scenario_id}/1"
    return f"/v/{token}/site/{scenario_id}"


def _launch_metadata(
    summary: CatalogSummary,
    target_role: str,
    delay_profile: str,
) -> dict[str, object]:
    return {
        "channel": summary.channel,
        "attack_type": summary.attack_type,
        "target_role": target_role,
        "delay_profile": delay_profile,
    }


def _event_payload(event) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "timestamp": serialize_utc_datetime(event.timestamp),
        "session_id": event.session_id,
        "scenario_id": event.scenario_id,
        "event_type": event.event_type,
        "source": event.source,
        "metadata": event.metadata_,
    }


def _attack_phase(attack) -> str:
    return (
        "AWAITING_MANUAL_END"
        if attack.state.get("destination_reached")
        and attack.status == "ENGAGED"
        else attack.status
    )


def _attack_payload(
    attack,
    event_count: int | None = None,
    events: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    phase = _attack_phase(attack)
    return {
        "attack_id": attack.attack_id,
        "delivery_id": attack.attack_id,
        "session_id": attack.operator_session_id,
        "run_id": attack.run_id,
        "scenario_id": attack.scenario_id,
        "channel": attack.channel,
        "status": attack.status,
        "phase": phase,
        "delivery_due_at": serialize_utc_datetime(attack.delivery_due_at),
        "delivered_at": (
            serialize_utc_datetime(attack.delivered_at)
            if attack.delivered_at
            else None
        ),
        "engaged_at": (
            serialize_utc_datetime(attack.engaged_at)
            if attack.engaged_at
            else None
        ),
        "completed_at": (
            serialize_utc_datetime(attack.completed_at)
            if attack.completed_at
            else None
        ),
        "victim_path": _victim_path(
            attack.channel,
            attack.victim_token,
            attack.scenario_id,
        ),
        "event_count": event_count,
        "events": events or [],
        "state": attack.state,
    }


async def _refresh_attack_delivery(
    database_session: OrmSession,
    attack,
) -> bool:
    service = SimulationAttackService(
        SimulationAttackRepository(database_session)
    )
    delivered = service.deliver_if_due(attack)
    if delivered:
        await emit_event(
            session=database_session,
            session_id=attack.operator_session_id,
            scenario_id=attack.scenario_id,
            event_type="message_delivered",
            source="victim",
            metadata={
                "channel": attack.channel,
                "attack_id": attack.attack_id,
                "delivery_id": attack.attack_id,
                "artifact_id": attack.scenario_id,
            },
        )
    return delivered


async def _start_run(
    request: Request,
    response: Response,
    database_session: OrmSession,
    summary: CatalogSummary,
    *,
    target_role: str,
    delay_profile: str,
) -> tuple[str, str, str]:
    session_id = ensure_simulation_session(
        request,
        response,
        database_session,
        scenario_id=summary.scenario_id,
        scenario_name=summary.title,
        scenario_type=summary.channel,
        description=summary.description,
    )
    state_service = SimulationStateService(
        SimulationRunRepository(database_session)
    )
    run = state_service.get_or_create(
        session_id=session_id,
        scenario_id=summary.scenario_id,
        channel=summary.channel,
        initial_state={"last_action": "scenario_started"},
    )
    attack_service = SimulationAttackService(
        SimulationAttackRepository(database_session)
    )
    existing_attack = attack_service.get_by_run_id(run.run_id)
    if existing_attack is not None:
        return session_id, run.run_id, existing_attack.attack_id
    environment = get_or_create_victim_environment(
        request,
        response,
        database_session,
    )
    attack = attack_service.create(
        run_id=run.run_id,
        operator_session_id=session_id,
        victim_session_id=environment.session_id,
        victim_token=environment.token,
        scenario_id=summary.scenario_id,
        channel=summary.channel,
        delay_profile=delay_profile,
    )
    await emit_event(
        session=database_session,
        session_id=session_id,
        scenario_id=summary.scenario_id,
        event_type="scenario_started",
        source="operator",
        metadata=_launch_metadata(summary, target_role, delay_profile),
    )
    await emit_event(
        session=database_session,
        session_id=session_id,
        scenario_id=summary.scenario_id,
        event_type="attack_armed",
        source="operator",
        metadata={
            "channel": summary.channel,
            "attack_type": summary.attack_type,
            "target_role": target_role,
            "attack_id": attack.attack_id,
        },
    )
    return session_id, run.run_id, attack.attack_id


def _validate_target_role(summary: CatalogSummary, value: str) -> str:
    if value not in TARGET_ROLE_CHOICES:
        raise HTTPException(
            status_code=422,
            detail="Choose one of the fictional target presets.",
        )
    if summary.target_role not in TARGET_ROLE_CHOICES:
        return summary.target_role
    return value


def _session_payload(session) -> dict[str, object]:
    return {
        "session_id": session.session_id,
        "scenario_id": session.scenario_id,
        "started_at": serialize_utc_datetime(session.started_at),
        "completed_at": (
            serialize_utc_datetime(session.completed_at)
            if session.completed_at
            else None
        ),
        "status": session.status,
    }


@router.get("/api/lab/dashboard")
async def lab_dashboard(
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> dict[str, object]:
    """Return fresh Lab state without forcing a full-page refresh."""
    attack_repository = SimulationAttackRepository(database_session)
    for attack in attack_repository.list_recent(limit=5):
        await _refresh_attack_delivery(database_session, attack)
    attacks = attack_repository.list_recent(limit=5)
    sessions = SessionRepository(database_session).list_recent(limit=5)
    return {
        "attacks": [_attack_payload(attack) for attack in attacks],
        "sessions": [_session_payload(session) for session in sessions],
    }


@router.get("/api/lab/scenarios")
def list_lab_scenarios(
    attack_type: str | None = Query(default=None, max_length=64),
    channel: str | None = Query(default=None, max_length=32),
) -> list[dict[str, object]]:
    summaries = catalog_summaries()
    if attack_type:
        summaries = tuple(
            summary
            for summary in summaries
            if summary.attack_type == attack_type
        )
    if channel:
        summaries = tuple(
            summary for summary in summaries if summary.channel == channel
        )
    return [
        {
            "scenario_id": summary.scenario_id,
            "attack_type": summary.attack_type,
            "channel": summary.channel,
            "brand": summary.brand,
            "title": summary.title,
            "description": summary.description,
            "target_role": summary.target_role,
            "indicators": list(summary.indicators),
            "delay_profile": summary.delay_profile,
            "launch_path": _launch_path(summary),
        }
        for summary in summaries
    ]


@router.post("/api/lab/launch")
async def launch_lab_scenario_api(
    launch: LabLaunchRequest,
    request: Request,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> JSONResponse:
    summary = _summary(launch.scenario_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Scenario not found.")
    target_role = _validate_target_role(summary, launch.target_role)
    cookie_response = Response()
    try:
        session_id, run_id, attack_id = await _start_run(
            request,
            cookie_response,
            database_session,
            summary,
            target_role=target_role,
            delay_profile=launch.delay_profile,
        )
    except SimulationStateError:
        raise HTTPException(
            status_code=422,
            detail="Unable to initialize the local simulation.",
        ) from None

    response_headers = {
        key: value
        for key, value in cookie_response.headers.items()
        if key.casefold() not in {"content-length", "set-cookie"}
    }
    attack = SimulationAttackService(
        SimulationAttackRepository(database_session)
    ).get_by_attack_id(attack_id)
    response = JSONResponse(
        content={
            "session_id": session_id,
            "run_id": run_id,
            "attack_id": attack_id,
            "scenario_id": summary.scenario_id,
            "launch_path": f"/lab/attacks/{attack_id}",
            "operator_path": f"/lab/attacks/{attack_id}",
            "victim_path": _victim_path(
                summary.channel,
                attack.victim_token,
                summary.scenario_id,
            ),
            "status": attack.status,
            "delivery_due_at": serialize_utc_datetime(attack.delivery_due_at),
            "target_role": target_role,
            "delay_profile": launch.delay_profile,
        },
        headers=response_headers,
    )
    for raw_key, raw_value in cookie_response.raw_headers:
        if raw_key.lower() == b"set-cookie":
            response.headers.append(
                "set-cookie",
                raw_value.decode("latin-1"),
            )
    return response


@router.get("/lab", response_class=HTMLResponse)
async def scenario_lab(
    request: Request,
    database_session: Annotated[OrmSession, Depends(get_session)],
    attack_type: str | None = Query(default=None, max_length=64),
    channel: str | None = Query(default=None, max_length=32),
) -> HTMLResponse:
    summaries = catalog_summaries()
    if attack_type:
        summaries = tuple(
            summary
            for summary in summaries
            if summary.attack_type == attack_type
        )
    if channel:
        summaries = tuple(
            summary for summary in summaries if summary.channel == channel
        )
    attack_repository = SimulationAttackRepository(database_session)
    for attack in attack_repository.list_recent(limit=5):
        await _refresh_attack_delivery(database_session, attack)
    active_attacks = attack_repository.list_recent(limit=5)
    recent_sessions = SessionRepository(database_session).list_recent(limit=5)
    active_attack_paths = {
        attack.attack_id: _victim_path(
            attack.channel,
            attack.victim_token,
            attack.scenario_id,
        )
        for attack in active_attacks
    }
    active_attack_phases = {
        attack.attack_id: _attack_phase(attack) for attack in active_attacks
    }
    return templates.TemplateResponse(
        request=request,
        name="lab.html",
        context={
            "summaries": summaries,
            "attack_types": attack_types(),
            "selected_attack_type": attack_type or "",
            "selected_channel": channel or "",
            "recent_sessions": recent_sessions,
            "active_attacks": active_attacks,
            "active_attack_paths": active_attack_paths,
            "active_attack_phases": active_attack_phases,
            "active_page": "lab",
        },
    )


@router.post("/lab/launch")
async def launch_lab_scenario_form(
    request: Request,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> RedirectResponse:
    form = await request.form()
    scenario_id = form.get("scenario_id", "")
    target_role = form.get("target_role", "")
    delay_profile = form.get("delay_profile", "short")
    if not all(
        isinstance(value, str)
        for value in (scenario_id, target_role, delay_profile)
    ):
        raise HTTPException(status_code=422, detail="Invalid launch selection.")
    assert isinstance(scenario_id, str)
    assert isinstance(target_role, str)
    assert isinstance(delay_profile, str)
    if delay_profile not in ("instant", "short", "standard"):
        raise HTTPException(status_code=422, detail="Invalid timing profile.")
    summary = _summary(scenario_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Scenario not found.")
    target_role = _validate_target_role(summary, target_role)
    response = RedirectResponse(
        "/lab",
        status_code=303,
    )
    try:
        _, _, attack_id = await _start_run(
            request,
            response,
            database_session,
            summary,
            target_role=target_role,
            delay_profile=delay_profile,
        )
    except SimulationStateError:
        raise HTTPException(
            status_code=422,
            detail="Unable to initialize the local simulation.",
        ) from None
    response.headers["location"] = f"/lab/attacks/{attack_id}"
    return response


@router.get("/api/lab/attacks/{attack_id}")
async def attack_status_api(
    attack_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> dict[str, object]:
    service = SimulationAttackService(
        SimulationAttackRepository(database_session)
    )
    try:
        attack = service.get_by_attack_id(attack_id)
    except SimulationAttackError:
        raise HTTPException(
            status_code=404, detail="Attack not found."
        ) from None
    await _refresh_attack_delivery(database_session, attack)
    events = EventRepository(database_session).list_by_session(
        attack.operator_session_id
    )
    return _attack_payload(
        attack,
        event_count=len(events),
        events=[_event_payload(event) for event in events],
    )


@router.get("/lab/attacks/{attack_id}", response_class=HTMLResponse)
async def attack_status_page(
    request: Request,
    attack_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    service = SimulationAttackService(
        SimulationAttackRepository(database_session)
    )
    try:
        attack = service.get_by_attack_id(attack_id)
    except SimulationAttackError:
        raise HTTPException(
            status_code=404, detail="Attack not found."
        ) from None
    await _refresh_attack_delivery(database_session, attack)
    events = EventRepository(database_session).list_by_session(
        attack.operator_session_id
    )
    return templates.TemplateResponse(
        request=request,
        name="attack_status.html",
        context={
            "attack": attack,
            "payload": _attack_payload(attack, event_count=len(events)),
            "events": events,
            "event_count": len(events),
            "victim_path": _victim_path(
                attack.channel,
                attack.victim_token,
                attack.scenario_id,
            ),
            "active_page": "lab",
        },
    )


@router.post("/api/lab/attacks/{attack_id}/abandon")
async def abandon_attack_api(
    attack_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> dict[str, object]:
    service = SimulationAttackService(
        SimulationAttackRepository(database_session)
    )
    try:
        attack = service.get_by_attack_id(attack_id)
        service.transition(attack, "ABANDONED")
    except SimulationAttackError:
        raise HTTPException(
            status_code=404, detail="Attack not found."
        ) from None
    await emit_event(
        session=database_session,
        session_id=attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="attack_abandoned",
        source="operator",
        metadata={
            "channel": attack.channel,
            "attack_id": attack.attack_id,
        },
    )
    complete_simulation_session(database_session, attack.operator_session_id)
    try:
        complete_simulation_session(database_session, attack.victim_session_id)
    except SessionNotFoundError:
        pass
    return _attack_payload(attack)
