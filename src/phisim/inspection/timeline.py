from pydantic import BaseModel, Field

from phisim.analysis.engine import analyze_event
from phisim.analysis.schemas import Indicator
from phisim.telemetry.schemas import EventResponse


class TimelineEntry(BaseModel):
    timestamp: str = Field(description="ISO 8601 formatted timestamp")
    event_type: str = Field(description="The underlying event type")
    description: str = Field(
        description="A human-readable explanation of the event"
    )
    indicators: list[Indicator] = Field(
        default_factory=list,
        description="Any phishing indicators identified during this event",
    )


def build_session_timeline(events: list[EventResponse]) -> list[TimelineEntry]:
    """
    Builds a chronological timeline of events for a session, combining raw
    telemetry with analysis indicators and human-readable explanations.
    """
    timeline = []

    # Sort events chronologically to build a sensible timeline
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    for event in sorted_events:
        event_indicators = analyze_event(event)

        # Map event types to human-readable explanations
        description = f"Interaction: {event.event_type}"
        if event.event_type == "credential_submission_attempted":
            description = (
                "Participant submitted credentials to the simulated form."
            )
        elif event.event_type == "page_viewed":
            description = "Participant viewed the simulation page."
        elif event.event_type == "email_opened":
            description = "Participant opened the simulated email message."
        elif event.event_type == "link_hovered":
            description = "Participant hovered over a link."
        elif event.event_type == "link_clicked":
            description = "Participant clicked on a link."
        elif event.event_type == "mfa_prompt_displayed":
            description = (
                "Participant was prompted for multi-factor authentication."
            )

        timeline.append(
            TimelineEntry(
                timestamp=event.timestamp.isoformat(),
                event_type=event.event_type,
                description=description,
                indicators=event_indicators,
            )
        )

    return timeline
