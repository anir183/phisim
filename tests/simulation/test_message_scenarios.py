import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.models.event import Event
from phisim.infra.sqlite.repos.event import EventRepository
from phisim.simulation.catalog import EMAIL_MESSAGES, SMS_THREADS

ARTIFACTS = [
    *(
        (message.message_id, "email", f"/inbox/{message.message_id}")
        for message in EMAIL_MESSAGES
    ),
    *(
        (thread.thread_id, "sms", f"/sms/{thread.thread_id}")
        for thread in SMS_THREADS
    ),
]


def _list_events(engine: Engine, session_id: str) -> list[Event]:
    with Session(engine) as session:
        repository = EventRepository(session)
        return repository.list_by_session(session_id)


def test_index_lists_every_channel(client: TestClient) -> None:
    response = client.get("/simulation")

    assert response.status_code == 200
    assert "/inbox/" in response.text
    assert "/sms/" in response.text
    assert "/qr/qr-phish-001" in response.text
    assert "/mfa/mfa-fatigue-001/1" in response.text
    assert "/scenario/credential-basic-001" in response.text


@pytest.mark.parametrize("artifact_id,channel,view_path", ARTIFACTS)
def test_every_message_artifact_opens_link_and_stays_local(
    client: TestClient,
    test_engine: Engine,
    artifact_id: str,
    channel: str,
    view_path: str,
) -> None:
    opened = client.get(view_path)
    assert opened.status_code == 200
    session_id = opened.cookies.get("phisim_session")
    assert session_id

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == ["message_opened"]
    assert events[0].scenario_id == artifact_id
    assert events[0].metadata_["channel"] == channel
    assert events[0].metadata_["content"]
    assert events[0].metadata_["subject"]
    assert events[0].source == "browser"

    following_path = (
        f"/inbox/{artifact_id}/link"
        if channel == "email"
        else f"/sms/{artifact_id}/link"
    )
    followed = client.get(following_path)

    assert followed.status_code == 200
    assert followed.history
    assert followed.history[0].status_code == 302
    location = followed.history[0].headers["location"]
    assert location.startswith("http://testserver")
    assert location.endswith("/scenario/credential-basic-001")

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == [
        "message_opened",
        "link_clicked",
        "scenario_opened",
    ]
    assert events[1].scenario_id == artifact_id
    assert events[1].metadata_["channel"] == channel
    assert events[1].metadata_["target_url"] == "/scenario/credential-basic-001"
    assert events[1].metadata_["content"]
    assert events[-1].scenario_id == "credential-basic-001"
    assert all(event.session_id == session_id for event in events)
