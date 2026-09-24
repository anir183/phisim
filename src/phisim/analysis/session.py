from phisim.analysis.engine import analyze_event
from phisim.analysis.schemas import Indicator
from phisim.telemetry.schemas import EventResponse


def aggregate_session_indicators(
    events: list[EventResponse],
) -> list[Indicator]:
    """
    Aggregates indicators across all events in a session.
    Provides a deduplicated summary of the phishing tactics observed.
    """
    all_indicators = []
    seen_codes = set()

    for event in events:
        event_indicators = analyze_event(event)
        for indicator in event_indicators:
            # Deduplicate by indicator code at the session level
            if indicator.code not in seen_codes:
                all_indicators.append(indicator)
                seen_codes.add(indicator.code)

    return all_indicators
