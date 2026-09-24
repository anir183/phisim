# ruff: noqa: B008

from secrets import token_hex

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from phisim.infra.sqlite.connection import get_session
from phisim.simulation.catalog import SCENARIOS, Scenario, get_scenario
from phisim.simulation.emit import emit_event
from phisim.telemetry.service import DuplicateEventError
from phisim.utils.paths import TEMPLATES_DIR

SESSION_COOKIE = "phisim_session"
_SESSION_HEX = frozenset("0123456789abcdef")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR / "simulation"))

router = APIRouter(tags=["simulation"])


def _valid_session_id(value: str | None) -> str | None:
    if value is None or not 1 <= len(value) <= 64:
        return None
    if any(char not in _SESSION_HEX for char in value):
        return None
    return value


def _ensure_session_id(request: Request, response: HTMLResponse) -> str:
    session_id = _valid_session_id(request.cookies.get(SESSION_COOKIE))
    if session_id is None:
        session_id = token_hex(16)
        response.set_cookie(
            SESSION_COOKIE,
            session_id,
            httponly=True,
            samesite="lax",
            path="/",
        )
    return session_id


async def _emit(
    session: Session,
    session_id: str,
    scenario: Scenario,
    event_type: str,
    metadata: dict[str, object],
) -> None:
    try:
        await emit_event(
            session=session,
            session_id=session_id,
            scenario_id=scenario.scenario_id,
            event_type=event_type,
            source="browser",
            metadata=metadata,
        )
    except DuplicateEventError:
        pass


@router.get("/simulation", response_class=HTMLResponse)
async def simulation_index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"scenarios": SCENARIOS},
    )


@router.get("/scenario/{scenario_id}", response_class=HTMLResponse)
async def scenario_login(
    request: Request,
    scenario_id: str,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    scenario = get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found.")

    response = templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"scenario": scenario},
    )

    session_id = _ensure_session_id(request, response)

    await _emit(
        session=session,
        session_id=session_id,
        scenario=scenario,
        event_type="scenario_opened",
        metadata={"channel": scenario.channel},
    )

    return response


@router.post("/scenario/{scenario_id}", response_class=HTMLResponse)
async def scenario_submit(
    request: Request,
    scenario_id: str,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    scenario = get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found.")

    form = await request.form()
    username_value = form.get("username", "")
    password_value = form.get("password", "")

    field_presence = {
        "username": bool(username_value),
        "password": bool(password_value),
    }
    result = "submitted" if all(field_presence.values()) else "incomplete"

    response = templates.TemplateResponse(
        request=request,
        name="outcome.html",
        context={
            "scenario": scenario,
            "result": result,
        },
    )

    session_id = _ensure_session_id(request, response)

    await _emit(
        session=session,
        session_id=session_id,
        scenario=scenario,
        event_type="credential_submission_attempted",
        metadata={
            "channel": scenario.channel,
            "interaction_result": result,
            "field_presence": field_presence,
        },
    )

    return response
