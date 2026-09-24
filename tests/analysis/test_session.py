from phisim.analysis.session import aggregate_session_indicators
from tests.analysis.test_engine import create_mock_event


def test_aggregate_session_indicators_deduplicates():
    events = [
        create_mock_event(
            "page_viewed", {"content": "Your account will be disabled today."}
        ),
        create_mock_event(
            "email_opened", {"content": "Immediate action required!"}
        ),
    ]

    # Both events trigger urgent_language indicator
    indicators = aggregate_session_indicators(events)

    assert len(indicators) == 1
    assert indicators[0].code == "urgent_language"


def test_aggregate_session_indicators_multiple_codes():
    events = [
        create_mock_event(
            "page_viewed", {"content": "Your account will be disabled today."}
        ),
        create_mock_event(
            "email_opened", {"subject": "Message from the IT Department"}
        ),
    ]

    indicators = aggregate_session_indicators(events)

    assert len(indicators) == 2
    codes = {ind.code for ind in indicators}
    assert codes == {"urgent_language", "authority_impersonation"}
