from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.models.event import Event
from phisim.infra.sqlite.repos.event import EventRepository

SCENARIO_ID = "qr-phish-001"
WEBSITE_ID = "credential-basic-001"


def _list_events(engine: Engine, session_id: str) -> list[Event]:
    with Session(engine) as session:
        repository = EventRepository(session)
        return repository.list_by_session(session_id)


def test_qr_page_renders_local_code_and_emits_view(
    client: TestClient,
    test_engine: Engine,
) -> None:
    response = client.get(f"/qr/{SCENARIO_ID}")

    assert response.status_code == 200
    assert "data:image/png;base64," in response.text
    assert f"/qr/{SCENARIO_ID}/scan" in response.text
    assert "http://testserver" in response.text

    session_id = response.cookies.get("phisim_session")
    assert session_id

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == ["qr_viewed"]
    assert events[0].scenario_id == SCENARIO_ID
    assert events[0].metadata_["channel"] == "qr"
    assert events[0].metadata_["subject"] == "Verification Required"
    assert events[0].metadata_["requests_credentials"] is True
    assert events[0].metadata_["incident_fear"] is True


def test_qr_scan_redirects_locally_and_emits_click(
    client: TestClient,
    test_engine: Engine,
) -> None:
    opened = client.get(f"/qr/{SCENARIO_ID}")
    session_id = opened.cookies.get("phisim_session")
    assert session_id

    response = client.get(f"/qr/{SCENARIO_ID}/scan")

    assert response.status_code == 200
    assert response.history
    assert response.history[0].status_code == 302
    location = response.history[0].headers["location"]
    assert location.startswith("http://testserver")
    assert location.endswith("/scenario/credential-basic-001")

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == [
        "qr_viewed",
        "link_clicked",
        "scenario_opened",
    ]
    assert events[1].scenario_id == SCENARIO_ID
    assert events[1].metadata_["channel"] == "qr"
    assert events[1].metadata_["target_url"] == "/scenario/credential-basic-001"
    assert events[1].metadata_["content"]
    assert events[-1].scenario_id == "credential-basic-001"


def test_qr_routes_reject_unknown_and_other_channels(
    client: TestClient,
) -> None:
    assert client.get("/qr/does-not-exist").status_code == 404
    assert client.get("/qr/does-not-exist/scan").status_code == 404
    assert client.get(f"/qr/{WEBSITE_ID}").status_code == 404
    assert client.get(f"/qr/{WEBSITE_ID}/scan").status_code == 404
    assert client.get(f"/scenario/{SCENARIO_ID}").status_code == 404
