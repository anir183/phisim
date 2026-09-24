from typing import Any

from pydantic import BaseModel, Field

from phisim.analysis.engine import analyze_event
from phisim.analysis.schemas import Indicator
from phisim.telemetry.schemas import EventResponse
from phisim.utils.datetime import serialize_utc_datetime


class TimelineEntry(BaseModel):
    event_id: str = Field(description="Stable Event identifier")
    session_id: str = Field(description="Session grouping identifier")
    scenario_id: str = Field(description="Scenario identifier")
    timestamp: str = Field(description="ISO 8601 UTC timestamp")
    event_type: str = Field(description="The underlying event type")
    source: str = Field(description="The component that emitted the Event")
    description: str = Field(
        description="A human-readable explanation of the event"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Validated, non-secret Event metadata",
    )
    indicators: list[Indicator] = Field(
        default_factory=list,
        description="Any phishing indicators identified during this event",
    )


_DESCRIPTIONS = {
    "scenario_opened": "Participant opened the simulated scenario.",
    "page_viewed": "Participant viewed the simulation page.",
    "message_opened": "Participant opened the simulated message.",
    "email_opened": "Participant opened the simulated email message.",
    "link_clicked": "Participant clicked a link in the simulation.",
    "link_hovered": "Participant hovered over a link.",
    "attachment_opened": "Participant opened a simulated attachment.",
    "qr_viewed": "Participant viewed the simulated QR verification flow.",
    "mfa_prompt_displayed": (
        "Participant was prompted for multi-factor authentication."
    ),
    "mfa_prompt_responded": "Participant responded to an MFA prompt.",
    "credential_submission_attempted": (
        "Participant submitted credentials to the simulated form."
    ),
}


def _description(event_type: str) -> str:
    return _DESCRIPTIONS.get(
        event_type,
        f"Participant interaction: {event_type}",
    )


def build_session_timeline(events: list[EventResponse]) -> list[TimelineEntry]:
    """Build a chronological, UTC-normalized explanation of Session Events."""
    timeline: list[TimelineEntry] = []

    for event in sorted(events, key=lambda item: item.timestamp):
        timeline.append(
            TimelineEntry(
                event_id=event.event_id,
                session_id=event.session_id,
                scenario_id=event.scenario_id,
                timestamp=serialize_utc_datetime(event.timestamp),
                event_type=event.event_type,
                source=event.source,
                description=_description(event.event_type),
                metadata=event.metadata,
                indicators=analyze_event(event),
            )
        )

    return timeline
