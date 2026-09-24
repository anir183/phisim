# ruff: noqa: B008

import base64
from io import BytesIO

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from phisim.infra.sqlite.connection import get_session
from phisim.simulation.catalog import (
    EMAIL_MESSAGES,
    INDICATOR_INFO,
    MFA_SCENARIOS,
    SCENARIOS,
    SMS_THREADS,
    get_email_message,
    get_mfa_scenario,
    get_scenario,
    get_sms_thread,
)
from phisim.simulation.emit import emit_event
from phisim.simulation.lifecycle import (
    complete_simulation_session,
    ensure_simulation_session,
)
from phisim.telemetry.service import DuplicateEventError
from phisim.utils.paths import TEMPLATES_DIR

CREDENTIAL_SITE_PATH = "/scenario/credential-basic-001"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR / "simulation"))

router = APIRouter(tags=["simulation"])


def _redirect_to_credential_site(
    request: Request,
    database_session: Session,
    *,
    scenario_id: str,
    scenario_name: str,
    scenario_type: str,
    description: str,
) -> tuple[RedirectResponse, str]:
    location = request.url_for(
        "scenario_login",
        scenario_id="credential-basic-001",
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


async def _emit(
    session: Session,
    session_id: str,
    *,
    scenario_id: str,
    event_type: str,
    metadata: dict[str, object],
) -> None:
    try:
        await emit_event(
            session=session,
            session_id=session_id,
            scenario_id=scenario_id,
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
        context={
            "website_scenarios": [
                scenario
                for scenario in SCENARIOS
                if scenario.channel == "website"
            ],
            "qr_scenarios": [
                scenario for scenario in SCENARIOS if scenario.channel == "qr"
            ],
            "email_messages": EMAIL_MESSAGES,
            "sms_threads": SMS_THREADS,
            "mfa_scenarios": MFA_SCENARIOS,
        },
    )


@router.get("/scenario/{scenario_id}", response_class=HTMLResponse)
async def scenario_login(
    request: Request,
    scenario_id: str,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "website":
        raise HTTPException(status_code=404, detail="Scenario not found.")

    response = templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"scenario": scenario},
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

    await _emit(
        session=session,
        session_id=session_id,
        scenario_id=scenario.scenario_id,
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
    if scenario is None or scenario.channel != "website":
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
            "indicator_info": INDICATOR_INFO,
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

    await _emit(
        session=session,
        session_id=session_id,
        scenario_id=scenario.scenario_id,
        event_type="credential_submission_attempted",
        metadata={
            "channel": scenario.channel,
            "interaction_result": result,
            "field_presence": field_presence,
        },
    )
    complete_simulation_session(session, session_id)

    return response


@router.get("/inbox", response_class=HTMLResponse)
async def inbox(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="inbox.html",
        context={"messages": EMAIL_MESSAGES},
    )


@router.get("/inbox/{message_id}", response_class=HTMLResponse)
async def email_view(
    request: Request,
    message_id: str,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    message = get_email_message(message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found.")

    response = templates.TemplateResponse(
        request=request,
        name="email.html",
        context={"message": message},
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

    await _emit(
        session=session,
        session_id=session_id,
        scenario_id=message.message_id,
        event_type="message_opened",
        metadata={"channel": "email"},
    )

    return response


@router.get("/inbox/{message_id}/link")
async def email_link(
    request: Request,
    message_id: str,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    message = get_email_message(message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found.")

    response, session_id = _redirect_to_credential_site(
        request,
        session,
        scenario_id=message.message_id,
        scenario_name=message.subject,
        scenario_type="email",
        description=message.body,
    )

    await _emit(
        session=session,
        session_id=session_id,
        scenario_id=message.message_id,
        event_type="link_clicked",
        metadata={
            "channel": "email",
            "target_url": CREDENTIAL_SITE_PATH,
        },
    )

    return response


@router.get("/inbox/{message_id}/attachment")
async def email_attachment(
    request: Request,
    message_id: str,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    message = get_email_message(message_id)
    if message is None or message.attachment_name is None:
        raise HTTPException(status_code=404, detail="Attachment not found.")

    location = request.url_for(
        "email_view",
        message_id=message.message_id,
    )
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

    await _emit(
        session=session,
        session_id=session_id,
        scenario_id=message.message_id,
        event_type="attachment_opened",
        metadata={
            "channel": "email",
            "attachment_name": message.attachment_name,
        },
    )

    return response


@router.get("/sms", response_class=HTMLResponse)
async def sms_inbox(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="sms.html",
        context={"threads": SMS_THREADS},
    )


@router.get("/sms/{thread_id}", response_class=HTMLResponse)
async def sms_view(
    request: Request,
    thread_id: str,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    thread = get_sms_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    response = templates.TemplateResponse(
        request=request,
        name="sms_thread.html",
        context={"thread": thread},
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

    await _emit(
        session=session,
        session_id=session_id,
        scenario_id=thread.thread_id,
        event_type="message_opened",
        metadata={"channel": "sms"},
    )

    return response


@router.get("/sms/{thread_id}/link")
async def sms_link(
    request: Request,
    thread_id: str,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    thread = get_sms_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    response, session_id = _redirect_to_credential_site(
        request,
        session,
        scenario_id=thread.thread_id,
        scenario_name=thread.sender_label,
        scenario_type="sms",
        description=" ".join(thread.messages),
    )

    await _emit(
        session=session,
        session_id=session_id,
        scenario_id=thread.thread_id,
        event_type="link_clicked",
        metadata={
            "channel": "sms",
            "target_url": CREDENTIAL_SITE_PATH,
        },
    )

    return response


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
    session: Session = Depends(get_session),
) -> HTMLResponse:
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "qr":
        raise HTTPException(status_code=404, detail="Scenario not found.")

    scan_url = str(request.url_for("qr_scan", scenario_id=scenario.scenario_id))
    response = templates.TemplateResponse(
        request=request,
        name="qr.html",
        context={
            "scenario": scenario,
            "qr_data_uri": _qr_data_uri(scan_url),
            "scan_url": scan_url,
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

    await _emit(
        session=session,
        session_id=session_id,
        scenario_id=scenario.scenario_id,
        event_type="qr_viewed",
        metadata={"channel": "qr"},
    )

    return response


@router.get("/qr/{scenario_id}/scan")
async def qr_scan(
    request: Request,
    scenario_id: str,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    scenario = get_scenario(scenario_id)
    if scenario is None or scenario.channel != "qr":
        raise HTTPException(status_code=404, detail="Scenario not found.")

    response, session_id = _redirect_to_credential_site(
        request,
        session,
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.title,
        scenario_type=scenario.channel,
        description=scenario.message,
    )

    await _emit(
        session=session,
        session_id=session_id,
        scenario_id=scenario.scenario_id,
        event_type="link_clicked",
        metadata={
            "channel": "qr",
            "target_url": CREDENTIAL_SITE_PATH,
        },
    )

    return response


def _parse_mfa_step(step_raw: str, prompt_count: int) -> int:
    try:
        step = int(step_raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=404, detail="Prompt not found."
        ) from exc
    if not 1 <= step <= prompt_count:
        raise HTTPException(status_code=404, detail="Prompt not found.")
    return step


@router.get("/mfa/{scenario_id}/{step}", response_class=HTMLResponse)
async def mfa_prompt(
    request: Request,
    scenario_id: str,
    step: str,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    scenario = get_mfa_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found.")

    current_step = _parse_mfa_step(step, scenario.prompt_count)

    response = templates.TemplateResponse(
        request=request,
        name="mfa.html",
        context={
            "scenario": scenario,
            "step": current_step,
        },
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

    await _emit(
        session=session,
        session_id=session_id,
        scenario_id=scenario.scenario_id,
        event_type="mfa_prompt_displayed",
        metadata={
            "channel": "website",
            "step": current_step,
            "total_steps": scenario.prompt_count,
        },
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
    session: Session = Depends(get_session),
) -> HTMLResponse | RedirectResponse:
    scenario = get_mfa_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found.")

    current_step = _parse_mfa_step(step, scenario.prompt_count)

    form = await request.form()
    action = form.get("action", "")
    if action not in ("approve", "deny"):
        raise HTTPException(status_code=400, detail="Invalid action.")

    fatigued = action == "approve" and current_step == scenario.prompt_count
    denied = action == "deny"

    if not fatigued and not denied:
        location = request.url_for(
            "mfa_prompt",
            scenario_id=scenario.scenario_id,
            step=str(current_step + 1),
        )
        response = RedirectResponse(str(location), status_code=302)
        session_id = ensure_simulation_session(
            request,
            response,
            session,
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.title,
            scenario_type="mfa",
            description=scenario.message,
        )

        await _emit(
            session=session,
            session_id=session_id,
            scenario_id=scenario.scenario_id,
            event_type="mfa_prompt_responded",
            metadata={
                "channel": "website",
                "step": current_step,
                "action": action,
            },
        )

        return response

    response = templates.TemplateResponse(
        request=request,
        name="mfa_outcome.html",
        context={
            "scenario": scenario,
            "fatigued": fatigued,
            "indicator_info": INDICATOR_INFO,
        },
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

    await _emit(
        session=session,
        session_id=session_id,
        scenario_id=scenario.scenario_id,
        event_type="mfa_prompt_responded",
        metadata={
            "channel": "website",
            "step": current_step,
            "action": action,
        },
    )
    complete_simulation_session(session, session_id)

    return response
