from __future__ import annotations

import base64
from io import BytesIO
from typing import Annotated

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.connection import get_session
from phisim.simulation.catalog import get_scenario
from phisim.simulation.channels.common import (
    emit_simulation_event,
    get_or_create_run,
    redirect_to_credential_site,
    templates,
)
from phisim.simulation.evidence import qr_evidence
from phisim.simulation.lifecycle import ensure_simulation_session

router = APIRouter(tags=["simulation"])


def _qr_data_uri(url: str) -> str:
    image = qrcode.make(url)
    buffer = BytesIO()
    image.save(buffer, "PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


@router.get("/qr/{scenario_id}", response_class=HTMLResponse)
async def qr_view(
    request: Request,
    scenario_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "qr":
        raise HTTPException(status_code=404, detail="Scenario not found.")
    scan_url = str(request.url_for("qr_scan", scenario_id=scenario.scenario_id))
    response = templates.TemplateResponse(
        request=request,
        name="simulation/qr.html",
        context={
            "scenario": scenario,
            "qr_data_uri": _qr_data_uri(scan_url),
            "scan_url": scan_url,
            "active_page": "simulation",
        },
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
        channel="qr",
    )
    await emit_simulation_event(
        session,
        session_id,
        scenario_id=scenario.scenario_id,
        event_type="qr_viewed",
        metadata=qr_evidence(scenario),
    )
    return response


@router.get("/qr/{scenario_id}/scan")
async def qr_scan(
    request: Request,
    scenario_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> RedirectResponse:
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "qr":
        raise HTTPException(status_code=404, detail="Scenario not found.")
    target_scenario_id = scenario.target_scenario_id or "credential-basic-001"
    response, session_id = redirect_to_credential_site(
        request,
        session,
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.title,
        scenario_type=scenario.channel,
        description=scenario.message,
        target_scenario_id=target_scenario_id,
    )
    await emit_simulation_event(
        session,
        session_id,
        scenario_id=scenario.scenario_id,
        event_type="qr_scan_simulated",
        metadata=qr_evidence(scenario)
        | {"target_url": f"/scenario/{target_scenario_id}"},
    )
    return response
