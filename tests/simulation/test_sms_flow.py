from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.models.event import Event
from phisim.infra.sqlite.repos.event import EventRepository

THREAD_ID = "sms-parcel-001"


def _list_events(engine: Engine, session_id: str) -> list[Event]:
    with Session(engine) as session:
        repository = EventRepository(session)
        return repository.list_by_session(session_id)


def test_sms_list_renders_threads(client: TestClient) -> None:
    response = client.get("/sms")

    assert response.status_code == 200
    assert THREAD_ID in response.text
    assert "sms-tech-support-001" in response.text


def test_sms_view_emits_message_open(
    client: TestClient,
    test_engine: Engine,
) -> None:
    response = client.get(f"/sms/{THREAD_ID}")

    assert response.status_code == 200
    assert "held at the local delivery center." in response.text

    session_id = response.cookies.get("phisim_session")
    assert session_id

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == ["message_opened"]
    assert events[0].scenario_id == THREAD_ID
    assert events[0].metadata_["channel"] == "sms"
    assert events[0].metadata_["subject"] == "Northstar Parcel"
    assert events[0].metadata_["content"]
    assert events[0].metadata_["requests_credentials"] is True

    sms_again = client.get("/sms")
    marker = f'data-thread-id="{THREAD_ID}"'
    marker_index = sms_again.text.index(marker)
    item_start = sms_again.text.rfind("<a", 0, marker_index)
    item_end = sms_again.text.index("</a>", marker_index)
    assert "unread" not in sms_again.text[item_start:item_end]


def test_sms_link_redirects_locally_and_emits_click(
    client: TestClient,
    test_engine: Engine,
) -> None:
    opened = client.get(f"/sms/{THREAD_ID}")
    session_id = opened.cookies.get("phisim_session")
    assert session_id

    response = client.get(f"/sms/{THREAD_ID}/link")

    assert response.status_code == 200
    assert response.history
    assert response.history[0].status_code == 302
    location = response.history[0].headers["location"]
    assert location.startswith("http://testserver")
    assert location.endswith("/scenario/credential-shopping-001")
    assert "Amazaun" in response.text

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == [
        "message_opened",
        "link_clicked",
        "scenario_opened",
    ]
    assert events[1].metadata_["channel"] == "sms"
    assert (
        events[1].metadata_["target_url"] == "/scenario/credential-shopping-001"
    )
    assert events[1].metadata_["subject"] == "Northstar Parcel"
    assert events[-1].scenario_id == "credential-shopping-001"
    assert all(event.session_id == session_id for event in events)


def test_unknown_thread_paths_return_404(client: TestClient) -> None:
    for path in (
        "/sms/does-not-exist",
        "/sms/does-not-exist/link",
        f"/sms/{THREAD_ID}/link/extra",
    ):
        assert client.get(path).status_code == 404
