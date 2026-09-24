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
from phisim.infra.sqlite.repos.session import SessionRepository
from phisim.infra.sqlite.repos.simulation_run import SimulationRunRepository
from phisim.simulation.catalog import (
    CatalogSummary,
    attack_types,
    catalog_summaries,
)
from phisim.simulation.emit import emit_event
from phisim.simulation.lifecycle import ensure_simulation_session
from phisim.simulation.state import SimulationStateError, SimulationStateService
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


def _launch_url(summary: CatalogSummary, delay_profile: str) -> str:
    return f"{_launch_path(summary)}?delay={delay_profile}"


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


async def _start_run(
    request: Request,
    response: Response,
    database_session: OrmSession,
    summary: CatalogSummary,
    *,
    target_role: str,
    delay_profile: str,
) -> tuple[str, str]:
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
    await emit_event(
        session=database_session,
        session_id=session_id,
        scenario_id=summary.scenario_id,
        event_type="scenario_started",
        source="operator",
        metadata=_launch_metadata(summary, target_role, delay_profile),
    )
    return session_id, run.run_id


def _validate_target_role(summary: CatalogSummary, value: str) -> str:
    if value not in TARGET_ROLE_CHOICES:
        raise HTTPException(
            status_code=422,
            detail="Choose one of the fictional target presets.",
        )
    if summary.target_role not in TARGET_ROLE_CHOICES:
        return summary.target_role
    return value


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
        session_id, run_id = await _start_run(
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
        if key.casefold() != "content-length"
    }
    return JSONResponse(
        content={
            "session_id": session_id,
            "run_id": run_id,
            "scenario_id": summary.scenario_id,
            "launch_path": _launch_path(summary),
            "target_role": target_role,
            "delay_profile": launch.delay_profile,
        },
        headers=response_headers,
    )


@router.get("/lab", response_class=HTMLResponse)
def scenario_lab(
    request: Request,
    database_session: Annotated[OrmSession, Depends(get_session)],
    attack_type: str | None = Query(default=None, max_length=64),
    channel: str | None = Query(default=None, max_length=32),
    target_role: str | None = Query(default=None, max_length=64),
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
    if target_role:
        summaries = tuple(
            summary
            for summary in summaries
            if summary.target_role == target_role
        )
    recent_sessions = SessionRepository(database_session).list_recent(limit=5)
    return templates.TemplateResponse(
        request=request,
        name="lab.html",
        context={
            "summaries": summaries,
            "attack_types": attack_types(),
            "selected_attack_type": attack_type or "",
            "selected_channel": channel or "",
            "selected_target_role": target_role or "",
            "target_roles": sorted(TARGET_ROLE_CHOICES),
            "recent_sessions": recent_sessions,
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
        _launch_url(summary, delay_profile),
        status_code=303,
    )
    try:
        await _start_run(
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
    return response
