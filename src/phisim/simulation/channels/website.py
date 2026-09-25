from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.connection import get_session
from phisim.simulation.catalog import INDICATOR_INFO, Scenario, get_scenario
from phisim.simulation.channels.common import (
    emit_simulation_event,
    get_or_create_run,
    get_run_state,
    templates,
    timing_context,
    update_run_state,
)
from phisim.simulation.evidence import scenario_evidence
from phisim.simulation.lifecycle import (
    complete_simulation_session,
    ensure_simulation_session,
)
from phisim.simulation.site_themes import get_site_theme

router = APIRouter(tags=["simulation"])


async def _complete_credential_submission(
    request: Request,
    scenario: Scenario,
    database_session: OrmSession,
    *,
    username_present: bool,
    password_value: object,
    session_id: str | None = None,
) -> HTMLResponse:
    result = (
        "submitted"
        if username_present and bool(password_value)
        else "incomplete"
    )
    response = templates.TemplateResponse(
        request=request,
        name="victim_destination.html",
        context={
            "scenario": scenario,
            "site_theme": get_site_theme(
                scenario.scenario_id, scenario.channel
            ),
            "end_url": request.url_for(
                "scenario_end", scenario_id=scenario.scenario_id
            ),
            "active_page": "simulation",
        },
    )
    session_id = ensure_simulation_session(
        request,
        response,
        database_session,
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.title,
        scenario_type=scenario.channel,
        description=scenario.message,
        session_id=session_id,
    )
    run = get_or_create_run(
        database_session,
        session_id=session_id,
        scenario_id=scenario.scenario_id,
        channel=scenario.channel,
        initial_state={"auth_stage": "destination"},
    )
    update_run_state(
        database_session,
        run.run_id,
        {"auth_stage": "destination", "last_action": "destination_reached"},
    )
    await emit_simulation_event(
        database_session,
        session_id,
        scenario_id=scenario.scenario_id,
        event_type="credential_submission_attempted",
        metadata={
            "channel": scenario.channel,
            "interaction_result": result,
            "field_presence": {
                "username": username_present,
                "password": bool(password_value),
            },
        },
    )
    await emit_simulation_event(
        database_session,
        session_id,
        scenario_id=scenario.scenario_id,
        event_type="destination_reached",
        source="victim",
        metadata={
            "channel": scenario.channel,
            "attack_type": scenario.attack_type,
            "action": "credential_submission_attempted",
        },
    )
    return response


@router.get("/scenario/{scenario_id}", response_class=HTMLResponse)
async def scenario_login(
    request: Request,
    scenario_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "website":
        raise HTTPException(status_code=404, detail="Scenario not found.")

    response = templates.TemplateResponse(
        request=request,
        name="simulation/login.html",
        context=timing_context(
            request,
            scenario=scenario,
            site_theme=get_site_theme(scenario.scenario_id, scenario.channel),
            active_page="simulation",
        ),
    )
    session_id = ensure_simulation_session(
        request,
        response,
        session,
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.title,
        scenario_type=scenario.channel,
        description=scenario.message,
    )
    get_or_create_run(
        session,
        session_id=session_id,
        scenario_id=scenario.scenario_id,
        channel=scenario.channel,
        initial_state={"auth_stage": "username"},
    )
    await emit_simulation_event(
        session,
        session_id,
        scenario_id=scenario.scenario_id,
        event_type="scenario_opened",
        metadata=scenario_evidence(scenario),
    )
    return response


@router.post(
    "/scenario/{scenario_id}/username",
    response_class=HTMLResponse,
    response_model=None,
)
async def scenario_username(
    request: Request,
    scenario_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse | RedirectResponse:
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "website":
        raise HTTPException(status_code=404, detail="Scenario not found.")
    form = await request.form()
    username_value = form.get("username", "")
    if not isinstance(username_value, str) or not username_value.strip():
        return templates.TemplateResponse(
            request=request,
            name="simulation/login.html",
            context=timing_context(
                request,
                scenario=scenario,
                site_theme=get_site_theme(
                    scenario.scenario_id, scenario.channel
                ),
                active_page="simulation",
                error="Enter a username to continue.",
            ),
        )
    response = RedirectResponse(
        str(
            request.url_for(
                "scenario_password",
                scenario_id=scenario.scenario_id,
            )
        ),
        status_code=303,
    )
    session_id = ensure_simulation_session(
        request,
        response,
        session,
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.title,
        scenario_type=scenario.channel,
        description=scenario.message,
    )
    run = get_or_create_run(
        session,
        session_id=session_id,
        scenario_id=scenario.scenario_id,
        channel=scenario.channel,
        initial_state={"auth_stage": "username"},
    )
    update_run_state(
        session,
        run.run_id,
        {"auth_stage": "password", "username_present": True},
    )
    return response


@router.get(
    "/scenario/{scenario_id}/password",
    response_class=HTMLResponse,
)
async def scenario_password(
    request: Request,
    scenario_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "website":
        raise HTTPException(status_code=404, detail="Scenario not found.")
    response = templates.TemplateResponse(
        request=request,
        name="simulation/password.html",
        context=timing_context(
            request,
            scenario=scenario,
            site_theme=get_site_theme(scenario.scenario_id, scenario.channel),
            active_page="simulation",
        ),
    )
    session_id = ensure_simulation_session(
        request,
        response,
        session,
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.title,
        scenario_type=scenario.channel,
        description=scenario.message,
    )
    get_or_create_run(
        session,
        session_id=session_id,
        scenario_id=scenario.scenario_id,
        channel=scenario.channel,
        initial_state={"auth_stage": "password"},
    )
    return response


@router.post(
    "/scenario/{scenario_id}/password",
    response_class=HTMLResponse,
    response_model=None,
)
async def scenario_password_submit(
    request: Request,
    scenario_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "website":
        raise HTTPException(status_code=404, detail="Scenario not found.")
    form = await request.form()
    password_value = form.get("password", "")
    if not password_value and scenario.scenario_id == "credential-shopping-001":
        password_value = form.get("payment_method", "")
    cookie_response = Response()
    session_id = ensure_simulation_session(
        request,
        cookie_response,
        session,
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.title,
        scenario_type=scenario.channel,
        description=scenario.message,
    )
    run = get_or_create_run(
        session,
        session_id=session_id,
        scenario_id=scenario.scenario_id,
        channel=scenario.channel,
        initial_state={"auth_stage": "password"},
    )
    state = get_run_state(session, run.run_id)
    return await _complete_credential_submission(
        request,
        scenario,
        session,
        username_present=bool(state.get("username_present")),
        password_value=password_value,
        session_id=session_id,
    )


@router.post("/scenario/{scenario_id}", response_class=HTMLResponse)
async def scenario_submit(
    request: Request,
    scenario_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "website":
        raise HTTPException(status_code=404, detail="Scenario not found.")
    form = await request.form()
    password_value = form.get("password", "")
    if not password_value and scenario.scenario_id == "credential-shopping-001":
        password_value = form.get("payment_method", "")
    return await _complete_credential_submission(
        request,
        scenario,
        session,
        username_present=bool(form.get("username", "")),
        password_value=password_value,
    )


@router.post("/scenario/{scenario_id}/end", response_class=HTMLResponse)
async def scenario_end(
    request: Request,
    scenario_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "website":
        raise HTTPException(status_code=404, detail="Scenario not found.")
    cookie_response = Response()
    session_id = ensure_simulation_session(
        request,
        cookie_response,
        session,
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.title,
        scenario_type=scenario.channel,
        description=scenario.message,
    )
    run = get_or_create_run(
        session,
        session_id=session_id,
        scenario_id=scenario.scenario_id,
        channel=scenario.channel,
        initial_state={"auth_stage": "landing"},
    )
    state = get_run_state(session, run.run_id)
    was_complete = state.get("auth_stage") == "complete"
    ended_early = (
        state.get("completion_outcome") == "ended_by_user"
        if was_complete
        else state.get("auth_stage") != "destination"
    )
    completion_outcome = "ended_by_user" if ended_early else "training_complete"
    if not was_complete:
        update_run_state(
            session,
            run.run_id,
            {
                "auth_stage": "complete",
                "completion_outcome": completion_outcome,
                "last_action": "scenario_completed",
            },
        )
        await emit_simulation_event(
            session,
            session_id,
            scenario_id=scenario.scenario_id,
            event_type="attack_completed",
            metadata={
                "channel": scenario.channel,
                "attack_type": scenario.attack_type,
                "outcome": completion_outcome,
            },
        )
        await emit_simulation_event(
            session,
            session_id,
            scenario_id=scenario.scenario_id,
            event_type="scenario_completed",
            metadata={
                "channel": scenario.channel,
                "attack_type": scenario.attack_type,
                "outcome": completion_outcome,
            },
        )
    response = templates.TemplateResponse(
        request=request,
        name="simulation/outcome.html",
        context=timing_context(
            request,
            scenario=scenario,
            site_theme=get_site_theme(scenario.scenario_id, scenario.channel),
            result="ended",
            ended_early=ended_early,
            indicator_info=INDICATOR_INFO,
            active_page="simulation",
        ),
    )
    for cookie in cookie_response.headers.getlist("set-cookie"):
        response.headers.append("set-cookie", cookie)
    complete_simulation_session(session, session_id)
    return response
