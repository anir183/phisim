from __future__ import annotations

import base64
from io import BytesIO
from typing import Annotated, Any

import qrcode
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.connection import get_session
from phisim.infra.sqlite.repos.simulation_attack import (
    SimulationAttackRepository,
)
from phisim.infra.sqlite.repos.simulation_environment import (
    SimulationEnvironmentRepository,
)
from phisim.sessions.service import SessionNotFoundError
from phisim.simulation.attack import (
    SimulationAttackError,
    SimulationAttackService,
)
from phisim.simulation.catalog import (
    INDICATOR_INFO,
    MFA_SCENARIOS,
    get_email_message,
    get_scenario,
    get_sms_thread,
)
from phisim.simulation.channels.common import emit_simulation_event, templates
from phisim.simulation.environment import (
    VICTIM_CONTEXT_COOKIE,
    get_or_create_victim_environment,
)
from phisim.simulation.evidence import (
    email_attachment_evidence,
    email_evidence,
    email_link_evidence,
    mfa_evidence,
    scenario_evidence,
    sms_evidence,
    sms_link_evidence,
)
from phisim.simulation.lifecycle import complete_simulation_session
from phisim.simulation.site_themes import get_site_theme
from phisim.utils.datetime import serialize_utc_datetime

router = APIRouter(tags=["victim-environment"])


def _attack_service(database_session: OrmSession) -> SimulationAttackService:
    return SimulationAttackService(SimulationAttackRepository(database_session))


def _get_attack(database_session: OrmSession, token: str):
    try:
        return _attack_service(database_session).get_by_token(token)
    except SimulationAttackError:
        raise HTTPException(
            status_code=404, detail="Victim context not found."
        ) from None


def _get_attack_optional(database_session: OrmSession, token: str):
    return _attack_service(database_session).get_active_by_token(token)


def _get_environment(database_session: OrmSession, token: str):
    environment = SimulationEnvironmentRepository(
        database_session
    ).get_by_token(token)
    if environment is None:
        raise HTTPException(status_code=404, detail="Victim context not found.")
    return environment


def _payload(attack) -> dict[str, object]:
    return {
        "attack_id": attack.attack_id,
        "delivery_id": attack.attack_id,
        "status": attack.status,
        "channel": attack.channel,
        "scenario_id": attack.scenario_id,
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
        "state": attack.state,
    }


async def _deliver_if_due(database_session: OrmSession, attack) -> bool:
    service = _attack_service(database_session)
    delivered = service.deliver_if_due(attack)
    if delivered:
        await emit_simulation_event(
            database_session,
            attack.operator_session_id,
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


async def _refresh_attack_history(
    database_session: OrmSession,
    token: str,
) -> list:
    for attack in _attack_history(database_session, token):
        await _deliver_if_due(database_session, attack)
    return _attack_history(database_session, token)


def _engage(database_session: OrmSession, attack) -> None:
    service = _attack_service(database_session)
    if attack.status == "DELIVERED":
        service.transition(attack, "ENGAGED")


def _delivery_metadata(attack) -> dict[str, str]:
    return {
        "attack_id": attack.attack_id,
        "delivery_id": attack.attack_id,
    }


def _require_context(attack) -> None:
    if attack.status in {"DRAFT", "ARMED", "LAUNCHING"}:
        raise HTTPException(
            status_code=404, detail="Victim context is not ready."
        )
    if attack.status in {"ABANDONED", "EXPIRED", "BLOCKED"}:
        raise HTTPException(status_code=410, detail="Victim context is closed.")


def _require_artifact_context(attack) -> None:
    """Allow terminal contexts to be listed, but not opened or acted on."""
    _require_context(attack)
    if attack.status == "COMPLETED":
        raise HTTPException(status_code=410, detail="Victim context is closed.")


def _require_target(attack, scenario_id: str) -> None:
    expected = attack.scenario_id
    if attack.channel == "email":
        message = get_email_message(attack.scenario_id)
        expected = (
            message.target_scenario_id if message is not None else expected
        )
    elif attack.channel == "sms":
        thread = get_sms_thread(attack.scenario_id)
        expected = thread.target_scenario_id if thread is not None else expected
    elif attack.channel == "qr":
        scenario = get_scenario(attack.scenario_id)
        expected = (
            scenario.target_scenario_id or expected if scenario else expected
        )
    if scenario_id != expected:
        raise HTTPException(status_code=404, detail="Website not found.")


async def _record_website_viewed(
    database_session: OrmSession,
    attack,
    scenario,
) -> None:
    service = _attack_service(database_session)
    if attack.state.get("website_viewed"):
        return
    if attack.status == "DELIVERED":
        _engage(database_session, attack)
    await emit_simulation_event(
        database_session,
        attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="website_viewed",
        source="victim",
        metadata=scenario_evidence(scenario) | _delivery_metadata(attack),
    )
    service.update_state(attack, {"website_viewed": True})


def _message_payload(message: Any, *, attack: bool) -> dict[str, object]:
    if attack:
        return {
            "message_id": message.message_id,
            "sender_label": message.sender_label,
            "sender_address": message.sender_address,
            "subject": message.subject,
            "preview": message.preview,
            "body": message.body,
            "timestamp": message.timestamp,
            "folder": message.folder,
            "unread": True,
            "is_attack": True,
            "attachment_name": message.attachment_name,
            "attachment_preview": message.attachment_preview,
            "spoofed_url": message.spoofed_url,
            "target_scenario_id": message.target_scenario_id,
        }
    return {
        "message_id": message.message_id,
        "sender_label": message.sender_label,
        "sender_address": message.sender_address,
        "subject": message.subject,
        "preview": message.preview,
        "body": message.body,
        "timestamp": message.timestamp,
        "folder": message.folder,
        "unread": message.unread,
        "is_attack": False,
    }


def _attack_history(database_session: OrmSession, token: str) -> list:
    return SimulationAttackRepository(database_session).list_by_victim_token(
        token
    )


def _email_messages_for_history(
    attacks: list,
    *,
    folder: str = "inbox",
    query: str = "",
) -> list[dict[str, object]]:
    messages: list[dict[str, object]] = []
    normalized_query = query.casefold().strip()
    for attack in attacks:
        if attack.channel != "email":
            continue
        for message_id in attack.state.get("delivered_message_ids", []):
            attack_message = get_email_message(message_id)
            if attack_message is None:
                continue
            starred = message_id in attack.state.get("starred_message_ids", [])
            archived = message_id in attack.state.get(
                "archived_message_ids", []
            )
            deleted = message_id in attack.state.get("deleted_message_ids", [])
            if folder == "inbox" and (archived or deleted):
                continue
            if folder == "starred" and (not starred or deleted):
                continue
            if folder == "trash" and not deleted:
                continue
            if folder not in {"inbox", "starred", "trash"}:
                continue
            if (
                normalized_query
                and normalized_query
                not in " ".join(
                    (
                        attack_message.sender_label,
                        attack_message.subject,
                        attack_message.preview,
                        attack_message.body,
                    )
                ).casefold()
            ):
                continue
            message = _message_payload(attack_message, attack=True)
            delivered_at = attack.delivered_at or attack.updated_at
            message["delivery_id"] = attack.attack_id
            message["timestamp"] = serialize_utc_datetime(delivered_at)
            message["starred"] = starred
            message["archived"] = archived
            message["deleted"] = deleted
            message["unread"] = message_id not in attack.state.get(
                "read_message_ids", []
            )
            messages.append(message)
    return messages


def _sms_threads_for_history(
    attacks: list,
    *,
    query: str = "",
) -> list[dict[str, object]]:
    threads: list[dict[str, object]] = []
    normalized_query = query.casefold().strip()
    for attack in attacks:
        if attack.channel != "sms":
            continue
        for thread_id in attack.state.get("delivered_thread_ids", []):
            attack_thread = get_sms_thread(thread_id)
            if attack_thread is None:
                continue
            if (
                normalized_query
                and normalized_query
                not in " ".join(
                    (
                        attack_thread.sender_label,
                        attack_thread.sender_number,
                        *attack_thread.messages,
                    )
                ).casefold()
            ):
                continue
            threads.append(
                {
                    "thread_id": attack_thread.thread_id,
                    "sender_label": attack_thread.sender_label,
                    "sender_number": attack_thread.sender_number,
                    "messages": attack_thread.messages,
                    "timestamp": serialize_utc_datetime(
                        attack.delivered_at or attack.updated_at
                    ),
                    "delivery_id": attack.attack_id,
                    "unread": (
                        thread_id not in attack.state.get("read_thread_ids", [])
                        and bool(attack_thread.unread)
                    ),
                    "typing": bool(attack_thread.typing_delay_ms),
                    "is_attack": True,
                }
            )
    return threads


def _set_environment_cookie(response, environment) -> None:
    response.set_cookie(
        VICTIM_CONTEXT_COOKIE,
        environment.token,
        httponly=True,
        samesite="lax",
        path="/",
    )


@router.get("/mail", response_class=HTMLResponse)
async def baseline_mail(
    request: Request,
    database_session: Annotated[OrmSession, Depends(get_session)],
    q: str | None = Query(default=None, max_length=64),
    folder: str = Query(default="inbox", max_length=16),
) -> HTMLResponse:
    cookie_response = Response()
    environment = get_or_create_victim_environment(
        request,
        cookie_response,
        database_session,
    )
    history = await _refresh_attack_history(
        database_session,
        environment.token,
    )
    active_attack = _get_attack_optional(database_session, environment.token)
    display_attack = active_attack or (history[0] if history else None)
    if display_attack is not None:
        response = templates.TemplateResponse(
            request=request,
            name="victim_mail.html",
            context={
                "attack": display_attack,
                "site_theme": get_site_theme(None, "email"),
                "messages": _email_messages_for_history(
                    history,
                    folder=folder,
                    query=q or "",
                ),
                "folder": folder,
                "search_query": q or "",
                "active_page": "victim",
            },
        )
    else:
        response = templates.TemplateResponse(
            request=request,
            name="environment_mail.html",
            context={
                "environment": {"victim_token": environment.token},
                "messages": [],
                "active_page": "victim",
            },
        )
    _set_environment_cookie(response, environment)
    return response


@router.get("/messages", response_class=HTMLResponse)
async def baseline_messages(
    request: Request,
    database_session: Annotated[OrmSession, Depends(get_session)],
    q: str | None = Query(default=None, max_length=64),
) -> HTMLResponse:
    cookie_response = Response()
    environment = get_or_create_victim_environment(
        request,
        cookie_response,
        database_session,
    )
    history = await _refresh_attack_history(
        database_session,
        environment.token,
    )
    active_attack = _get_attack_optional(database_session, environment.token)
    display_attack = active_attack or (history[0] if history else None)
    if display_attack is not None:
        response = templates.TemplateResponse(
            request=request,
            name="victim_messages.html",
            context={
                "attack": display_attack,
                "site_theme": get_site_theme(None, "sms"),
                "threads": _sms_threads_for_history(history, query=q or ""),
                "search_query": q or "",
                "active_page": "victim",
            },
        )
    else:
        response = templates.TemplateResponse(
            request=request,
            name="environment_messages.html",
            context={
                "environment": {"victim_token": environment.token},
                "threads": [],
                "active_page": "victim",
            },
        )
    _set_environment_cookie(response, environment)
    return response


@router.get("/v/{token}/status")
async def victim_status(
    token: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> dict[str, object]:
    _get_environment(database_session, token)
    attack = _attack_service(database_session).get_any_by_token(token)
    if attack is None:
        return {
            "status": "BASELINE",
            "state": {},
        }
    await _deliver_if_due(database_session, attack)
    return _payload(attack)


@router.get("/v/{token}/mail", response_class=HTMLResponse)
async def victim_mail(
    request: Request,
    token: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
    q: str | None = Query(default=None, max_length=64),
    folder: str = Query(default="inbox", max_length=16),
) -> HTMLResponse:
    _get_environment(database_session, token)
    history = await _refresh_attack_history(database_session, token)
    active_attack = _get_attack_optional(database_session, token)
    display_attack = active_attack or (history[0] if history else None)
    if display_attack is None:
        return templates.TemplateResponse(
            request=request,
            name="environment_mail.html",
            context={
                "environment": {"victim_token": token},
                "messages": [],
                "active_page": "victim",
            },
        )
    return templates.TemplateResponse(
        request=request,
        name="victim_mail.html",
        context={
            "attack": display_attack,
            "site_theme": get_site_theme(None, "email"),
            "messages": _email_messages_for_history(
                history,
                folder=folder,
                query=q or "",
            ),
            "folder": folder,
            "search_query": q or "",
            "active_page": "victim",
        },
    )


@router.get("/v/{token}/mail/{message_id}", response_class=HTMLResponse)
async def victim_email(
    request: Request,
    token: str,
    message_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
    delivery_id: str | None = None,
    folder: str = Query(default="inbox", max_length=16),
) -> HTMLResponse:
    _get_environment(database_session, token)
    history = await _refresh_attack_history(database_session, token)
    attack = next(
        (
            item
            for item in history
            if item.channel == "email"
            and message_id in item.state.get("delivered_message_ids", [])
            and (delivery_id is None or item.attack_id == delivery_id)
        ),
        None,
    )
    if attack is None:
        raise HTTPException(status_code=404, detail="Message not found.")
    _require_artifact_context(attack)
    attack_message = get_email_message(message_id)
    if attack_message is None:
        raise HTTPException(status_code=404, detail="Message not found.")
    _engage(database_session, attack)
    service = _attack_service(database_session)
    read_ids = set(attack.state.get("read_message_ids", []))
    read_ids.add(message_id)
    service.update_state(
        attack,
        {
            "read_message_ids": sorted(read_ids),
            "last_action": "message_opened",
        },
    )
    await emit_simulation_event(
        database_session,
        attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="message_opened",
        source="victim",
        metadata=email_evidence(attack_message) | _delivery_metadata(attack),
    )
    message = _message_payload(attack_message, attack=True)
    message["delivery_id"] = attack.attack_id
    message["timestamp"] = serialize_utc_datetime(
        attack.delivered_at or attack.updated_at
    )
    return templates.TemplateResponse(
        request=request,
        name="victim_email.html",
        context={
            "attack": attack,
            "site_theme": _site_theme_for_attack(attack),
            "message": message,
            "folder": folder,
            "active_page": "victim",
        },
    )


@router.post("/v/{token}/mail/{message_id}/state")
async def victim_email_state(
    request: Request,
    token: str,
    message_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
    action: str = Form(...),
    delivery_id: str | None = None,
    folder: str = Query(default="inbox", max_length=16),
) -> RedirectResponse:
    history = await _refresh_attack_history(database_session, token)
    attack = next(
        (
            item
            for item in history
            if item.channel == "email"
            and message_id in item.state.get("delivered_message_ids", [])
            and (delivery_id is None or item.attack_id == delivery_id)
        ),
        None,
    )
    if attack is None:
        raise HTTPException(status_code=404, detail="Message not found.")
    _require_artifact_context(attack)
    if action not in {
        "star",
        "unstar",
        "archive",
        "unarchive",
        "delete",
        "restore",
    }:
        raise HTTPException(status_code=400, detail="Invalid message action.")
    state = attack.state
    starred = set(state.get("starred_message_ids", []))
    archived = set(state.get("archived_message_ids", []))
    deleted = set(state.get("deleted_message_ids", []))
    if action == "star":
        starred.add(message_id)
    elif action == "unstar":
        starred.discard(message_id)
    elif action == "archive":
        archived.add(message_id)
    elif action == "unarchive":
        archived.discard(message_id)
    elif action == "delete":
        deleted.add(message_id)
    else:
        deleted.discard(message_id)
        archived.discard(message_id)
    service = _attack_service(database_session)
    service.update_state(
        attack,
        {
            "starred_message_ids": sorted(starred),
            "archived_message_ids": sorted(archived),
            "deleted_message_ids": sorted(deleted),
            "last_action": "message_state_changed",
        },
    )
    await emit_simulation_event(
        database_session,
        attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="message_state_changed",
        source="victim",
        metadata={"action": action, "folder": folder}
        | _delivery_metadata(attack),
    )
    return RedirectResponse(
        f"/v/{token}/mail?folder={folder}",
        status_code=303,
    )


@router.get(
    "/v/{token}/mail/{message_id}/attachment",
    response_class=HTMLResponse,
)
async def victim_attachment(
    request: Request,
    token: str,
    message_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
    delivery_id: str | None = None,
) -> HTMLResponse:
    history = await _refresh_attack_history(database_session, token)
    attack = next(
        (
            item
            for item in history
            if item.channel == "email"
            and message_id in item.state.get("delivered_message_ids", [])
            and (delivery_id is None or item.attack_id == delivery_id)
        ),
        None,
    )
    if attack is None:
        raise HTTPException(status_code=404, detail="Attachment not found.")
    _require_artifact_context(attack)
    message = get_email_message(message_id)
    if message is None or message.attachment_name is None:
        raise HTTPException(status_code=404, detail="Attachment not found.")
    _engage(database_session, attack)
    _attack_service(database_session).update_state(
        attack,
        {"attachment_opened": True, "last_action": "attachment_opened"},
    )
    await emit_simulation_event(
        database_session,
        attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="attachment_opened",
        source="victim",
        metadata=email_attachment_evidence(message)
        | _delivery_metadata(attack),
    )
    return templates.TemplateResponse(
        request=request,
        name="victim_attachment.html",
        context={
            "attack": attack,
            "site_theme": _site_theme_for_attack(attack),
            "message": message,
            "active_page": "victim",
        },
    )


@router.get("/v/{token}/mail/{message_id}/link")
async def victim_email_link(
    token: str,
    message_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
    delivery_id: str | None = None,
) -> RedirectResponse:
    history = await _refresh_attack_history(database_session, token)
    attack = next(
        (
            item
            for item in history
            if item.channel == "email"
            and message_id in item.state.get("delivered_message_ids", [])
            and (delivery_id is None or item.attack_id == delivery_id)
        ),
        None,
    )
    if attack is None:
        raise HTTPException(status_code=404, detail="Message link not found.")
    _require_artifact_context(attack)
    message = get_email_message(message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found.")
    _engage(database_session, attack)
    await emit_simulation_event(
        database_session,
        attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="link_clicked",
        source="victim",
        metadata=email_link_evidence(message) | _delivery_metadata(attack),
    )
    return RedirectResponse(
        url_for_victim_site(attack, message.target_scenario_id),
        status_code=302,
    )


def url_for_victim_site(attack, scenario_id: str) -> str:
    return f"/v/{attack.victim_token}/site/{scenario_id}"


def victim_return_path(attack) -> str:
    if attack.channel == "sms":
        return f"/v/{attack.victim_token}/messages"
    return f"/v/{attack.victim_token}/mail"


def _site_theme_for_attack(attack):
    return get_site_theme(attack.scenario_id, attack.channel)


def _site_theme_for_scenario(scenario):
    return get_site_theme(scenario.scenario_id, scenario.channel)


def _site_end_path(attack, scenario_id: str) -> str:
    return f"/v/{attack.victim_token}/site/{scenario_id}/end"


async def _complete_attack(
    request: Request,
    database_session: OrmSession,
    attack,
    scenario,
    *,
    outcome: str,
) -> HTMLResponse:
    service = _attack_service(database_session)
    if attack.status == "DELIVERED":
        _engage(database_session, attack)
    if attack.status == "ENGAGED":
        service.transition(attack, "COMPLETED")
    service.update_state(
        attack,
        {
            "processing": False,
            "result_revealed": True,
            "current_step": 4,
            "last_action": "attack_completed",
        },
    )
    if outcome == "ended_by_user":
        event_outcome = "ended_by_user"
    else:
        event_outcome = "training_complete"
    await emit_simulation_event(
        database_session,
        attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="attack_completed",
        source="victim",
        metadata={
            "channel": attack.channel,
            "attack_type": scenario.attack_type,
            "attack_id": attack.attack_id,
            "delivery_id": attack.attack_id,
            "outcome": event_outcome,
        },
    )
    await emit_simulation_event(
        database_session,
        attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="scenario_completed",
        source="victim",
        metadata={
            "channel": "website",
            "attack_type": scenario.attack_type,
            "attack_id": attack.attack_id,
            "delivery_id": attack.attack_id,
            "outcome": event_outcome,
        },
    )
    complete_simulation_session(database_session, attack.operator_session_id)
    try:
        complete_simulation_session(database_session, attack.victim_session_id)
    except SessionNotFoundError:
        pass
    return templates.TemplateResponse(
        request=request,
        name="victim_reveal.html",
        context={
            "attack": attack,
            "scenario": scenario,
            "site_theme": _site_theme_for_scenario(scenario),
            "indicator_info": INDICATOR_INFO,
            "return_path": victim_return_path(attack),
            "ended_early": outcome == "ended_by_user",
            "active_page": "victim",
        },
    )


@router.get("/v/{token}/messages", response_class=HTMLResponse)
async def victim_messages(
    request: Request,
    token: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
    q: str | None = Query(default=None, max_length=64),
) -> HTMLResponse:
    _get_environment(database_session, token)
    history = await _refresh_attack_history(database_session, token)
    active_attack = _get_attack_optional(database_session, token)
    display_attack = active_attack or (history[0] if history else None)
    if display_attack is None:
        return templates.TemplateResponse(
            request=request,
            name="environment_messages.html",
            context={
                "environment": {"victim_token": token},
                "threads": [],
                "active_page": "victim",
            },
        )
    return templates.TemplateResponse(
        request=request,
        name="victim_messages.html",
        context={
            "attack": display_attack,
            "site_theme": get_site_theme(None, "sms"),
            "threads": _sms_threads_for_history(history, query=q or ""),
            "search_query": q or "",
            "active_page": "victim",
        },
    )


@router.get("/v/{token}/messages/{thread_id}", response_class=HTMLResponse)
async def victim_message(
    request: Request,
    token: str,
    thread_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
    delivery_id: str | None = None,
) -> HTMLResponse:
    _get_environment(database_session, token)
    history = await _refresh_attack_history(database_session, token)
    attack = next(
        (
            item
            for item in history
            if item.channel == "sms"
            and thread_id in item.state.get("delivered_thread_ids", [])
            and (delivery_id is None or item.attack_id == delivery_id)
        ),
        None,
    )
    if attack is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    _require_artifact_context(attack)
    thread = next(
        (
            item
            for item in _sms_threads_for_history(history)
            if item["thread_id"] == thread_id
            and item["delivery_id"] == (delivery_id or attack.attack_id)
        ),
        None,
    )
    if thread is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if thread["is_attack"]:
        _engage(database_session, attack)
        service = _attack_service(database_session)
        read_ids = set(attack.state.get("read_thread_ids", []))
        read_ids.add(thread_id)
        service.update_state(
            attack,
            {
                "read_thread_ids": sorted(read_ids),
                "last_action": "message_opened",
            },
        )
        catalog_thread = get_sms_thread(thread_id)
        if catalog_thread is not None:
            await emit_simulation_event(
                database_session,
                attack.operator_session_id,
                scenario_id=attack.scenario_id,
                event_type="message_opened",
                source="victim",
                metadata=sms_evidence(catalog_thread)
                | _delivery_metadata(attack),
            )
    return templates.TemplateResponse(
        request=request,
        name="victim_message.html",
        context={
            "attack": attack,
            "site_theme": _site_theme_for_attack(attack),
            "thread": thread,
            "active_page": "victim",
        },
    )


@router.get("/v/{token}/messages/{thread_id}/link")
async def victim_message_link(
    token: str,
    thread_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
    delivery_id: str | None = None,
) -> RedirectResponse:
    history = await _refresh_attack_history(database_session, token)
    attack = next(
        (
            item
            for item in history
            if item.channel == "sms"
            and thread_id in item.state.get("delivered_thread_ids", [])
            and (delivery_id is None or item.attack_id == delivery_id)
        ),
        None,
    )
    if attack is None:
        raise HTTPException(status_code=404, detail="Message link not found.")
    _require_artifact_context(attack)
    thread = get_sms_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    _engage(database_session, attack)
    await emit_simulation_event(
        database_session,
        attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="link_clicked",
        source="victim",
        metadata=sms_link_evidence(thread) | _delivery_metadata(attack),
    )
    return RedirectResponse(
        url_for_victim_site(attack, thread.target_scenario_id),
        status_code=302,
    )


@router.get("/v/{token}/site/{scenario_id}", response_class=HTMLResponse)
async def victim_site(
    request: Request,
    token: str,
    scenario_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
    step: int = 1,
) -> HTMLResponse:
    attack = _get_attack(database_session, token)
    await _deliver_if_due(database_session, attack)
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "website":
        raise HTTPException(status_code=404, detail="Website not found.")
    _require_context(attack)
    _require_target(attack, scenario_id)
    await _record_website_viewed(database_session, attack, scenario)
    return templates.TemplateResponse(
        request=request,
        name="victim_site.html",
        context={
            "attack": attack,
            "scenario": scenario,
            "site_theme": _site_theme_for_scenario(scenario),
            "end_url": _site_end_path(attack, scenario.scenario_id),
            "step": max(1, min(step, 2)),
            "active_page": "victim",
        },
    )


@router.post("/v/{token}/site/{scenario_id}/continue")
async def victim_site_continue(
    request: Request,
    token: str,
    scenario_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> RedirectResponse:
    attack = _get_attack(database_session, token)
    await _deliver_if_due(database_session, attack)
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "website":
        raise HTTPException(status_code=404, detail="Website not found.")
    if attack.status == "DELIVERED":
        _engage(database_session, attack)
    _require_context(attack)
    _require_target(attack, scenario_id)
    await _record_website_viewed(database_session, attack, scenario)
    form = await request.form()
    identifier = form.get("identifier", "")
    if not isinstance(identifier, str) or not identifier.strip():
        raise HTTPException(status_code=422, detail="Identifier is required.")
    service = _attack_service(database_session)
    service.update_state(
        attack, {"current_step": 2, "last_action": "website_viewed"}
    )
    return RedirectResponse(
        f"/v/{token}/site/{scenario_id}?step=2",
        status_code=303,
    )


@router.post(
    "/v/{token}/site/{scenario_id}/finish",
    response_class=HTMLResponse,
    response_model=None,
)
async def victim_site_finish(
    request: Request,
    token: str,
    scenario_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse | RedirectResponse:
    attack = _get_attack(database_session, token)
    await _deliver_if_due(database_session, attack)
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "website":
        raise HTTPException(status_code=404, detail="Website not found.")
    if attack.status == "DELIVERED":
        _engage(database_session, attack)
    _require_context(attack)
    _require_target(attack, scenario_id)
    if attack.status not in {"ENGAGED", "COMPLETED"}:
        raise HTTPException(
            status_code=404, detail="Website context is not ready."
        )
    if attack.state.get("current_step", 1) < 2:
        raise HTTPException(
            status_code=422, detail="Complete the first step first."
        )
    await _record_website_viewed(database_session, attack, scenario)
    form = await request.form()
    value = form.get("password", form.get("confirmation", ""))
    service = _attack_service(database_session)
    service.update_state(
        attack,
        {
            "current_step": 3,
            "processing": True,
            "last_action": "processing_started",
        },
    )
    credential_flow = "password" in scenario.workflow
    if credential_flow:
        await emit_simulation_event(
            database_session,
            attack.operator_session_id,
            scenario_id=attack.scenario_id,
            event_type="credential_submission_attempted",
            source="victim",
            metadata={
                "channel": "website",
                "interaction_result": "submitted" if value else "incomplete",
                "field_presence": {
                    "username": True,
                    "password": bool(value),
                },
            },
        )
    else:
        await emit_simulation_event(
            database_session,
            attack.operator_session_id,
            scenario_id=attack.scenario_id,
            event_type="victim_action_completed",
            source="victim",
            metadata={
                "channel": "website",
                "action": "confirmation_submitted",
                "field_presence": {"confirmation": bool(value)},
                "attack_id": attack.attack_id,
            },
        )
    await emit_simulation_event(
        database_session,
        attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="processing_started",
        source="victim",
        metadata={
            "channel": "website",
            "attack_id": attack.attack_id,
            "workflow": list(scenario.workflow),
        },
    )
    return RedirectResponse(
        f"/v/{attack.victim_token}/site/{scenario_id}/result",
        status_code=303,
    )


@router.get("/v/{token}/site/{scenario_id}/result", response_class=HTMLResponse)
async def victim_result(
    request: Request,
    token: str,
    scenario_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    attack = _get_attack(database_session, token)
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "website":
        raise HTTPException(status_code=404, detail="Website not found.")
    _require_context(attack)
    _require_target(attack, scenario_id)
    if attack.status == "COMPLETED":
        return templates.TemplateResponse(
            request=request,
            name="victim_reveal.html",
            context={
                "attack": attack,
                "scenario": scenario,
                "site_theme": _site_theme_for_scenario(scenario),
                "indicator_info": INDICATOR_INFO,
                "return_path": victim_return_path(attack),
                "ended_early": False,
                "active_page": "victim",
            },
        )
    if not attack.state.get("processing"):
        raise HTTPException(status_code=404, detail="No pending result.")
    return await _complete_attack(
        request,
        database_session,
        attack,
        scenario,
        outcome="training_complete",
    )


@router.post(
    "/v/{token}/site/{scenario_id}/result", response_class=HTMLResponse
)
async def victim_result_submit(
    request: Request,
    token: str,
    scenario_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    attack = _get_attack(database_session, token)
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "website":
        raise HTTPException(status_code=404, detail="Website not found.")
    _require_context(attack)
    _require_target(attack, scenario_id)
    if attack.status == "COMPLETED":
        return templates.TemplateResponse(
            request=request,
            name="victim_reveal.html",
            context={
                "attack": attack,
                "scenario": scenario,
                "site_theme": _site_theme_for_scenario(scenario),
                "indicator_info": INDICATOR_INFO,
                "return_path": victim_return_path(attack),
                "ended_early": False,
                "active_page": "victim",
            },
        )
    if not attack.state.get("processing"):
        raise HTTPException(status_code=404, detail="No pending result.")
    return await _complete_attack(
        request,
        database_session,
        attack,
        scenario,
        outcome="training_complete",
    )


@router.post("/v/{token}/site/{scenario_id}/end")
async def victim_end_simulation(
    request: Request,
    token: str,
    scenario_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    attack = _get_attack(database_session, token)
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "website":
        raise HTTPException(status_code=404, detail="Website not found.")
    if attack.status == "COMPLETED":
        return templates.TemplateResponse(
            request=request,
            name="victim_reveal.html",
            context={
                "attack": attack,
                "scenario": scenario,
                "site_theme": _site_theme_for_scenario(scenario),
                "indicator_info": INDICATOR_INFO,
                "return_path": victim_return_path(attack),
                "ended_early": True,
                "active_page": "victim",
            },
        )
    _require_context(attack)
    _require_target(attack, scenario_id)
    return await _complete_attack(
        request,
        database_session,
        attack,
        scenario,
        outcome="ended_by_user",
    )


@router.get("/v/{token}/qr/{scenario_id}", response_class=HTMLResponse)
async def victim_qr(
    request: Request,
    token: str,
    scenario_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    attack = _get_attack(database_session, token)
    await _deliver_if_due(database_session, attack)
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "qr":
        raise HTTPException(status_code=404, detail="QR scenario not found.")
    _require_context(attack)
    if scenario_id != attack.scenario_id:
        raise HTTPException(status_code=404, detail="QR scenario not found.")
    scan_url = f"/v/{token}/qr/{scenario_id}/scan"
    image = qrcode.make(scan_url)
    buffer = BytesIO()
    image.save(buffer, "PNG")
    qr_data = base64.b64encode(buffer.getvalue()).decode("ascii")
    return templates.TemplateResponse(
        request=request,
        name="victim_qr.html",
        context={
            "attack": attack,
            "scenario": scenario,
            "site_theme": get_site_theme(
                scenario.target_scenario_id or scenario.scenario_id,
                "website",
            ),
            "qr_data_uri": f"data:image/png;base64,{qr_data}",
            "scan_url": scan_url,
            "active_page": "victim",
        },
    )


@router.get("/v/{token}/qr/{scenario_id}/scan")
async def victim_qr_scan(
    token: str,
    scenario_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> RedirectResponse:
    attack = _get_attack(database_session, token)
    await _deliver_if_due(database_session, attack)
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "qr":
        raise HTTPException(status_code=404, detail="QR scenario not found.")
    _require_context(attack)
    if scenario_id != attack.scenario_id:
        raise HTTPException(status_code=404, detail="QR scenario not found.")
    _engage(database_session, attack)
    await emit_simulation_event(
        database_session,
        attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="qr_scan_simulated",
        source="victim",
        metadata={
            "attack_id": attack.attack_id,
            "target_url": url_for_victim_site(
                attack, scenario.target_scenario_id or "credential-basic-001"
            ),
        },
    )
    return RedirectResponse(
        url_for_victim_site(
            attack, scenario.target_scenario_id or "credential-basic-001"
        ),
        status_code=302,
    )


@router.get("/v/{token}/mfa/{scenario_id}/{step}", response_class=HTMLResponse)
async def victim_mfa(
    request: Request,
    token: str,
    scenario_id: str,
    step: int,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse:
    attack = _get_attack(database_session, token)
    await _deliver_if_due(database_session, attack)
    scenario = next(
        (item for item in MFA_SCENARIOS if item.scenario_id == scenario_id),
        None,
    )
    if scenario is None or not 1 <= step <= scenario.prompt_count:
        raise HTTPException(status_code=404, detail="MFA prompt not found.")
    _require_context(attack)
    if scenario_id != attack.scenario_id:
        raise HTTPException(status_code=404, detail="MFA prompt not found.")
    if attack.status == "DELIVERED":
        _engage(database_session, attack)
    await emit_simulation_event(
        database_session,
        attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="mfa_prompt_displayed",
        source="victim",
        metadata=mfa_evidence(scenario, step) | _delivery_metadata(attack),
    )
    return templates.TemplateResponse(
        request=request,
        name="victim_mfa.html",
        context={
            "attack": attack,
            "scenario": scenario,
            "site_theme": get_site_theme(scenario.scenario_id, "mfa"),
            "step": step,
            "active_page": "victim",
        },
    )


@router.post(
    "/v/{token}/mfa/{scenario_id}/{step}",
    response_model=None,
)
async def victim_mfa_respond(
    request: Request,
    token: str,
    scenario_id: str,
    step: int,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> HTMLResponse | RedirectResponse:
    attack = _get_attack(database_session, token)
    await _deliver_if_due(database_session, attack)
    scenario = next(
        (item for item in MFA_SCENARIOS if item.scenario_id == scenario_id),
        None,
    )
    if scenario is None or not 1 <= step <= scenario.prompt_count:
        raise HTTPException(status_code=404, detail="MFA prompt not found.")
    _require_context(attack)
    if scenario_id != attack.scenario_id:
        raise HTTPException(status_code=404, detail="MFA prompt not found.")
    form = await request.form()
    action = form.get("action", "")
    if not isinstance(action, str) or action not in {"approve", "deny"}:
        raise HTTPException(status_code=400, detail="Invalid action.")
    _engage(database_session, attack)
    await emit_simulation_event(
        database_session,
        attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="mfa_prompt_responded",
        source="victim",
        metadata=mfa_evidence(scenario, step, action=action)
        | _delivery_metadata(attack),
    )
    terminal = action == "deny" or step == scenario.prompt_count
    if not terminal:
        return RedirectResponse(
            f"/v/{token}/mfa/{scenario_id}/{step + 1}",
            status_code=303,
        )
    service = _attack_service(database_session)
    if attack.status == "ENGAGED":
        service.transition(attack, "COMPLETED")
    await emit_simulation_event(
        database_session,
        attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="attack_completed",
        source="victim",
        metadata={"channel": "mfa", "attack_id": attack.attack_id},
    )
    await emit_simulation_event(
        database_session,
        attack.operator_session_id,
        scenario_id=attack.scenario_id,
        event_type="scenario_completed",
        source="victim",
        metadata={
            "channel": "mfa",
            "attack_type": scenario.attack_type,
            "attack_id": attack.attack_id,
            "outcome": "training_complete",
        },
    )
    complete_simulation_session(database_session, attack.operator_session_id)
    try:
        complete_simulation_session(database_session, attack.victim_session_id)
    except SessionNotFoundError:
        pass
    return templates.TemplateResponse(
        request=request,
        name="victim_reveal.html",
        context={
            "attack": attack,
            "scenario": scenario,
            "site_theme": get_site_theme(scenario.scenario_id, "mfa"),
            "indicator_info": INDICATOR_INFO,
            "return_path": victim_return_path(attack),
            "ended_early": False,
            "active_page": "victim",
        },
    )
