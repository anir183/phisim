from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from phisim.simulation.catalog import (
    EMAIL_MESSAGES,
    MFA_SCENARIOS,
    SCENARIOS,
    SMS_THREADS,
)
from phisim.simulation.channels.common import templates

router = APIRouter(tags=["simulation"])


@router.get("/simulation", response_class=HTMLResponse)
async def simulation_index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="simulation/index.html",
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
            "active_page": "simulation",
        },
    )
