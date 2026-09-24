from datetime import UTC, datetime

from phisim.analysis.engine import analyze_event
from phisim.telemetry.schemas import EventResponse


def create_mock_event(event_type: str, metadata: dict) -> EventResponse:
    return EventResponse(
        id=1,
        event_id="test-1",
        session_id="session-1",
        scenario_id="scenario-1",
        event_type=event_type,
        source="test",
        metadata=metadata,
        timestamp=datetime.now(UTC),
    )


def test_analyze_credential_submission():
    event = create_mock_event("credential_submission_attempted", {})
    indicators = analyze_event(event)

    assert len(indicators) == 1
    assert indicators[0].code == "credential_request"
    assert indicators[0].context == "high"


def test_analyze_urgent_language():
    event = create_mock_event(
        "page_viewed", {"content": "Your account will be disabled today."}
    )
    indicators = analyze_event(event)

    assert len(indicators) == 1
    assert indicators[0].code == "urgent_language"
    assert "disabled" in indicators[0].evidence.lower()


def test_analyze_authority_impersonation():
    event = create_mock_event(
        "email_opened", {"subject": "Message from the IT Department"}
    )
    indicators = analyze_event(event)

    assert len(indicators) == 1
    assert indicators[0].code == "authority_impersonation"
    assert "it department" in indicators[0].evidence.lower()


def test_analyze_domain_mismatch():
    event = create_mock_event(
        "link_hovered",
        {
            "visible_link": "https://company.com",
            "actual_target": "http://evil.com/login",
        },
    )
    indicators = analyze_event(event)

    assert len(indicators) == 1
    assert indicators[0].code == "domain_mismatch"


def test_analyze_unexpected_link():
    event = create_mock_event(
        "email_opened",
        {
            "link_url": "http://evil.com/reset-password",
        },
    )
    indicators = analyze_event(event)

    assert len(indicators) == 1
    assert indicators[0].code == "unexpected_link"


def test_analyze_suspicious_attachment():
    event = create_mock_event(
        "email_opened",
        {
            "attachment_name": "invoice.exe",
        },
    )
    indicators = analyze_event(event)

    assert len(indicators) == 1
    assert indicators[0].code == "suspicious_attachment"


def test_analyze_unusual_mfa_request():
    event = create_mock_event(
        "mfa_prompt_displayed",
        {
            "is_unusual_context": True,
        },
    )
    indicators = analyze_event(event)

    assert len(indicators) == 1
    assert indicators[0].code == "unusual_mfa_request"
