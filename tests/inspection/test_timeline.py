from datetime import UTC, datetime, timedelta

from phisim.inspection.timeline import build_session_timeline
from tests.analysis.test_engine import create_mock_event


def test_build_session_timeline_uses_event_names_and_utc() -> None:
    now = datetime.now(UTC)

    message = create_mock_event(
        "message_opened",
        {"subject": "Message from the IT Department"},
    )
    message.timestamp = now

    submission = create_mock_event("credential_submission_attempted", {})
    submission.timestamp = now + timedelta(minutes=1)

    timeline = build_session_timeline([submission, message])

    assert len(timeline) == 2
    assert [entry.event_type for entry in timeline] == [
        "message_opened",
        "credential_submission_attempted",
    ]
    assert all(entry.timestamp.endswith("Z") for entry in timeline)
    assert "it department" in str(timeline[0].indicators).lower()
    assert "credentials" in timeline[1].description.lower()
    assert timeline[0].session_id == "session-1"
    assert timeline[0].scenario_id == "scenario-1"
    assert timeline[0].event_id == "test-1"
