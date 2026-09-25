from __future__ import annotations

from dataclasses import replace
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.connection import get_session
from phisim.simulation.catalog import EMAIL_MESSAGES, get_email_message
from phisim.simulation.channels.common import (
    emit_simulation_event,
    get_or_create_run,
    get_run_state,
    redirect_to_credential_site,
    session_state_values,
    templates,
    update_run_state,
)
from phisim.simulation.evidence import (
    email_attachment_evidence,
    email_evidence,
    email_link_evidence,
)
from phisim.simulation.lifecycle import ensure_simulation_session
from phisim.simulation.site_themes import get_site_theme
from phisim.simulation.timing import timing_for_request, transition_delay_ms

router = APIRouter(tags=["simulation"])


@router.get("/inbox", response_class=HTMLResponse)
async def inbox(
    request: Request,
    session: Annotated[OrmSession, Depends(get_session)],
    q: str | None = Query(default=None, max_length=64),
) -> HTMLResponse:
    read_ids = session_state_values(request, session, "read_message_ids")
    query = q.casefold().strip() if q else ""
    messages = [
        replace(
            message,
            unread=message.unread and message.message_id not in read_ids,
        )
        for message in EMAIL_MESSAGES
        if not query
        or query
        in " ".join(
            (
                message.sender_label,
                message.subject,
                message.preview,
                message.body,
            )
        ).casefold()
    ]
    return templates.TemplateResponse(
        request=request,
        name="simulation/inbox.html",
        context={
            "messages": messages,
            "search_query": q or "",
            "site_theme": get_site_theme("email", "email"),
            "active_page": "simulation",
        },
    )


@router.get("/inbox/{message_id}", response_class=HTMLResponse)
async def email_view(
    request: Request,
    message_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    message = get_email_message(message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found.")
    delay_profile, _ = timing_for_request(request)
    response = templates.TemplateResponse(
        request=request,
        name="simulation/email.html",
        context={
            "message": message,
            "site_theme": get_site_theme(message.message_id, "email"),
            "transition_kind": "link",
            "transition_delay_ms": transition_delay_ms(
                "link",
                delay_profile,
            ),
            "active_page": "simulation",
        },
    )
    session_id = ensure_simulation_session(
        request,
        response,
        session,
        scenario_id=message.message_id,
        scenario_name=message.subject,
        scenario_type="email",
        description=message.body,
    )
    run = get_or_create_run(
        session,
        session_id=session_id,
        scenario_id=message.message_id,
        channel="email",
        initial_state={"read_message_ids": []},
    )
    state = get_run_state(session, run.run_id)
    read_ids = set(state.get("read_message_ids", []))
    read_ids.add(message.message_id)
    update_run_state(
        session,
        run.run_id,
        {
            "read_message_ids": sorted(read_ids),
            "last_action": "message_opened",
        },
    )
    await emit_simulation_event(
        session,
        session_id,
        scenario_id=message.message_id,
        event_type="message_opened",
        metadata=email_evidence(message),
    )
    return response


@router.get("/inbox/{message_id}/link")
async def email_link(
    request: Request,
    message_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> RedirectResponse:
    message = get_email_message(message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found.")
    response, session_id = redirect_to_credential_site(
        request,
        session,
        scenario_id=message.message_id,
        scenario_name=message.subject,
        scenario_type="email",
        description=message.body,
        target_scenario_id=message.target_scenario_id,
    )
    await emit_simulation_event(
        session,
        session_id,
        scenario_id=message.message_id,
        event_type="link_clicked",
        metadata=email_link_evidence(message),
    )
    return response


@router.get("/inbox/{message_id}/attachment/preview")
async def email_attachment_preview(
    request: Request,
    message_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    message = get_email_message(message_id)
    if message is None or message.attachment_name is None:
        raise HTTPException(status_code=404, detail="Attachment not found.")
    response = templates.TemplateResponse(
        request=request,
        name="simulation/attachment.html",
        context={
            "message": message,
            "site_theme": get_site_theme(message.message_id, "email"),
            "active_page": "simulation",
        },
    )
    session_id = ensure_simulation_session(
        request,
        response,
        session,
        scenario_id=message.message_id,
        scenario_name=message.subject,
        scenario_type="email",
        description=message.body,
    )
    run = get_or_create_run(
        session,
        session_id=session_id,
        scenario_id=message.message_id,
        channel="email",
    )
    update_run_state(
        session,
        run.run_id,
        {"attachment_opened": True, "last_action": "attachment_previewed"},
    )
    await emit_simulation_event(
        session,
        session_id,
        scenario_id=message.message_id,
        event_type="attachment_opened",
        metadata=email_attachment_evidence(message),
    )
    return response


@router.get("/inbox/{message_id}/attachment")
async def email_attachment(
    request: Request,
    message_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> RedirectResponse:
    message = get_email_message(message_id)
    if message is None or message.attachment_name is None:
        raise HTTPException(status_code=404, detail="Attachment not found.")
    location = request.url_for("email_view", message_id=message.message_id)
    response = RedirectResponse(str(location), status_code=302)
    session_id = ensure_simulation_session(
        request,
        response,
        session,
        scenario_id=message.message_id,
        scenario_name=message.subject,
        scenario_type="email",
        description=message.body,
    )
    await emit_simulation_event(
        session,
        session_id,
        scenario_id=message.message_id,
        event_type="attachment_opened",
        metadata=email_attachment_evidence(message),
    )
    return response
