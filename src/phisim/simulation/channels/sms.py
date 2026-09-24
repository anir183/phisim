from __future__ import annotations

from dataclasses import replace
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.connection import get_session
from phisim.simulation.catalog import SMS_THREADS, get_sms_thread
from phisim.simulation.channels.common import (
    emit_simulation_event,
    get_or_create_run,
    get_run_state,
    redirect_to_credential_site,
    session_state_values,
    templates,
    update_run_state,
)
from phisim.simulation.evidence import sms_evidence, sms_link_evidence
from phisim.simulation.lifecycle import ensure_simulation_session

router = APIRouter(tags=["simulation"])


@router.get("/sms", response_class=HTMLResponse)
async def sms_inbox(
    request: Request,
    session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    read_ids = session_state_values(request, session, "read_thread_ids")
    threads = [
        replace(
            thread,
            unread=0 if thread.thread_id in read_ids else thread.unread,
        )
        for thread in SMS_THREADS
    ]
    return templates.TemplateResponse(
        request=request,
        name="simulation/sms.html",
        context={"threads": threads, "active_page": "simulation"},
    )


@router.get("/sms/{thread_id}", response_class=HTMLResponse)
async def sms_view(
    request: Request,
    thread_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    thread = get_sms_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    response = templates.TemplateResponse(
        request=request,
        name="simulation/sms_thread.html",
        context={"thread": thread, "active_page": "simulation"},
    )
    session_id = ensure_simulation_session(
        request,
        response,
        session,
        scenario_id=thread.thread_id,
        scenario_name=thread.sender_label,
        scenario_type="sms",
        description=" ".join(thread.messages),
    )
    run = get_or_create_run(
        session,
        session_id=session_id,
        scenario_id=thread.thread_id,
        channel="sms",
        initial_state={"read_thread_ids": []},
    )
    state = get_run_state(session, run.run_id)
    read_ids = set(state.get("read_thread_ids", []))
    read_ids.add(thread.thread_id)
    update_run_state(
        session,
        run.run_id,
        {
            "read_thread_ids": sorted(read_ids),
            "last_action": "message_opened",
        },
    )
    await emit_simulation_event(
        session,
        session_id,
        scenario_id=thread.thread_id,
        event_type="message_opened",
        metadata=sms_evidence(thread),
    )
    return response


@router.get("/sms/{thread_id}/link")
async def sms_link(
    request: Request,
    thread_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> RedirectResponse:
    thread = get_sms_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    response, session_id = redirect_to_credential_site(
        request,
        session,
        scenario_id=thread.thread_id,
        scenario_name=thread.sender_label,
        scenario_type="sms",
        description=" ".join(thread.messages),
        target_scenario_id=thread.target_scenario_id,
    )
    await emit_simulation_event(
        session,
        session_id,
        scenario_id=thread.thread_id,
        event_type="link_clicked",
        metadata=sms_link_evidence(thread),
    )
    return response
