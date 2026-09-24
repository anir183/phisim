from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.connection import get_session
from phisim.simulation.catalog import INDICATOR_INFO, get_mfa_scenario
from phisim.simulation.channels.common import (
    emit_simulation_event,
    get_or_create_run,
    templates,
    timing_context,
    update_run_state,
)
from phisim.simulation.evidence import mfa_evidence
from phisim.simulation.lifecycle import (
    complete_simulation_session,
    ensure_simulation_session,
)

router = APIRouter(tags=["simulation"])


def _parse_mfa_step(step_raw: str, prompt_count: int) -> int:
    try:
        step = int(step_raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail="Prompt not found.",
        ) from exc
    if not 1 <= step <= prompt_count:
        raise HTTPException(status_code=404, detail="Prompt not found.")
    return step


@router.get("/mfa/{scenario_id}/{step}", response_class=HTMLResponse)
async def mfa_prompt(
    request: Request,
    scenario_id: str,
    step: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    scenario = get_mfa_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found.")
    current_step = _parse_mfa_step(step, scenario.prompt_count)
    response = templates.TemplateResponse(
        request=request,
        name="simulation/mfa.html",
        context=timing_context(
            request,
            scenario=scenario,
            step=current_step,
            active_page="simulation",
        ),
    )
    session_id = ensure_simulation_session(
        request,
        response,
        session,
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.title,
        scenario_type="mfa",
        description=scenario.message,
    )
    run = get_or_create_run(
        session,
        session_id=session_id,
        scenario_id=scenario.scenario_id,
        channel="mfa",
        initial_state={"mfa_step": current_step},
    )
    update_run_state(session, run.run_id, {"mfa_step": current_step})
    await emit_simulation_event(
        session,
        session_id,
        scenario_id=scenario.scenario_id,
        event_type="mfa_prompt_displayed",
        metadata=mfa_evidence(scenario, current_step),
    )
    return response


@router.post(
    "/mfa/{scenario_id}/{step}",
    response_class=HTMLResponse,
    response_model=None,
)
async def mfa_respond(
    request: Request,
    scenario_id: str,
    step: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse | RedirectResponse:
    scenario = get_mfa_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found.")
    current_step = _parse_mfa_step(step, scenario.prompt_count)
    form = await request.form()
    action_value = form.get("action", "")
    if not isinstance(action_value, str) or action_value not in (
        "approve",
        "deny",
    ):
        raise HTTPException(status_code=400, detail="Invalid action.")
    action = action_value
    fatigued = action == "approve" and current_step == scenario.prompt_count
    denied = action == "deny"

    if not fatigued and not denied:
        location = request.url_for(
            "mfa_prompt",
            scenario_id=scenario.scenario_id,
            step=str(current_step + 1),
        )
        response = RedirectResponse(
            f"{location}?delay={timing_context(request)['delay_profile']}",
            status_code=302,
        )
        session_id = ensure_simulation_session(
            request,
            response,
            session,
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.title,
            scenario_type="mfa",
            description=scenario.message,
        )
        run = get_or_create_run(
            session,
            session_id=session_id,
            scenario_id=scenario.scenario_id,
            channel="mfa",
            initial_state={"mfa_step": current_step},
        )
        update_run_state(session, run.run_id, {"mfa_step": current_step})
        await emit_simulation_event(
            session,
            session_id,
            scenario_id=scenario.scenario_id,
            event_type="mfa_prompt_responded",
            metadata=mfa_evidence(
                scenario,
                current_step,
                action=action,
            ),
        )
        return response

    response = templates.TemplateResponse(
        request=request,
        name="simulation/mfa_outcome.html",
        context=timing_context(
            request,
            scenario=scenario,
            fatigued=fatigued,
            indicator_info=INDICATOR_INFO,
            active_page="simulation",
        ),
    )
    session_id = ensure_simulation_session(
        request,
        response,
        session,
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.title,
        scenario_type="mfa",
        description=scenario.message,
    )
    run = get_or_create_run(
        session,
        session_id=session_id,
        scenario_id=scenario.scenario_id,
        channel="mfa",
        initial_state={"mfa_step": current_step},
    )
    update_run_state(session, run.run_id, {"mfa_step": current_step})
    await emit_simulation_event(
        session,
        session_id,
        scenario_id=scenario.scenario_id,
        event_type="mfa_prompt_responded",
        metadata=mfa_evidence(
            scenario,
            current_step,
            action=action,
        ),
    )
    await emit_simulation_event(
        session,
        session_id,
        scenario_id=scenario.scenario_id,
        event_type="scenario_completed",
        metadata={
            "channel": "mfa",
            "attack_type": scenario.attack_type,
            "outcome": "training_complete",
        },
    )
    complete_simulation_session(session, session_id)
    return response
