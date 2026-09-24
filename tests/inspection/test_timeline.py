from datetime import UTC, datetime, timedelta

from phisim.inspection.timeline import build_session_timeline
from tests.analysis.test_engine import create_mock_event


def test_build_session_timeline():
    now = datetime.now(UTC)

    event1 = create_mock_event(
        "email_opened", {"subject": "Message from the IT Department"}
    )
    event1.timestamp = now

    event2 = create_mock_event("credential_submission_attempted", {})
    event2.timestamp = now + timedelta(minutes=1)

    events = [event2, event1]  # Out of order to test sorting

    timeline = build_session_timeline(events)

    assert len(timeline) == 2

    # Chronologically sorted
    assert timeline[0].event_type == "email_opened"
    assert timeline[1].event_type == "credential_submission_attempted"

    # Descriptions are human-readable
    assert "it department" in str(timeline[0].indicators).lower()
    assert "credentials" in timeline[1].description.lower()
