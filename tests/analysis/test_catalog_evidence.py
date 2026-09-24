from datetime import UTC, datetime

from phisim.analysis.engine import analyze_event
from phisim.simulation.catalog import (
    EMAIL_MESSAGES,
    MFA_SCENARIOS,
    SCENARIOS,
    SMS_THREADS,
)
from phisim.simulation.evidence import (
    email_evidence,
    mfa_evidence,
    scenario_evidence,
    sms_evidence,
)
from phisim.telemetry.schemas import EventResponse


def _event(event_type: str, scenario_id: str, metadata: dict) -> EventResponse:
    return EventResponse(
        id=1,
        event_id=f"catalog-{scenario_id}-{event_type}",
        timestamp=datetime.now(UTC),
        session_id="catalog-session",
        scenario_id=scenario_id,
        event_type=event_type,
        source="test",
        metadata=metadata,
    )


def test_catalog_evidence_produces_deterministic_indicators() -> None:
    for scenario in SCENARIOS:
        indicators = analyze_event(
            _event(
                "scenario_opened",
                scenario.scenario_id,
                scenario_evidence(scenario),
            )
        )
        codes = {indicator.code for indicator in indicators}
        assert codes & set(scenario.indicators)

    for message in EMAIL_MESSAGES:
        indicators = analyze_event(
            _event(
                "message_opened",
                message.message_id,
                email_evidence(message),
            )
        )
        codes = {indicator.code for indicator in indicators}
        assert codes & set(message.indicators)

    for thread in SMS_THREADS:
        indicators = analyze_event(
            _event("message_opened", thread.thread_id, sms_evidence(thread))
        )
        codes = {indicator.code for indicator in indicators}
        assert codes & set(thread.indicators)

    for scenario in MFA_SCENARIOS:
        indicators = analyze_event(
            _event(
                "mfa_prompt_responded",
                scenario.scenario_id,
                mfa_evidence(
                    scenario,
                    scenario.prompt_count,
                    action="approve",
                ),
            )
        )
        codes = {indicator.code for indicator in indicators}
        assert "mfa_fatigue" in codes
