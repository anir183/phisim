from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.models.event import Event
from phisim.infra.sqlite.repos.event import EventRepository

MESSAGE_ID = "email-phish-001"
ATTACHMENT_MESSAGE_ID = "attachment-phish-001"


def _list_events(engine: Engine, session_id: str) -> list[Event]:
    with Session(engine) as session:
        repository = EventRepository(session)
        return repository.list_by_session(session_id)


def test_inbox_renders_and_lists_messages(client: TestClient) -> None:
    response = client.get("/inbox")

    assert response.status_code == 200
    assert MESSAGE_ID in response.text
    assert ATTACHMENT_MESSAGE_ID in response.text
    assert "Fictional Mailbox" in response.text


def test_email_view_assigns_session_and_emits_open(
    client: TestClient,
    test_engine: Engine,
) -> None:
    response = client.get(f"/inbox/{MESSAGE_ID}")

    assert response.status_code == 200
    assert "verify your mailbox" in response.text
    assert "techno-main-sl-access.net" in response.text

    session_id = response.cookies.get("phisim_session")
    assert session_id

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == ["message_opened"]
    assert events[0].scenario_id == MESSAGE_ID
    assert events[0].source == "browser"
    assert events[0].metadata_ == {"channel": "email"}


def test_email_link_redirects_locally_and_emits_click(
    client: TestClient,
    test_engine: Engine,
) -> None:
    opened = client.get(f"/inbox/{MESSAGE_ID}")
    session_id = opened.cookies.get("phisim_session")
    assert session_id

    response = client.get(f"/inbox/{MESSAGE_ID}/link")

    assert response.status_code == 200
    assert response.history
    assert response.history[0].status_code == 302
    location = response.history[0].headers["location"]
    assert location.startswith("http://testserver")
    assert location.endswith("/scenario/credential-basic-001")

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == [
        "message_opened",
        "link_clicked",
        "scenario_opened",
    ]
    link_clicked = events[1]
    assert link_clicked.scenario_id == MESSAGE_ID
    assert link_clicked.metadata_ == {
        "channel": "email",
        "target_url": "/scenario/credential-basic-001",
    }
    assert events[-1].scenario_id == "credential-basic-001"
    assert all(event.session_id == session_id for event in events)


def test_email_funnel_reaches_credential_site(client: TestClient) -> None:
    opened = client.get(f"/inbox/{MESSAGE_ID}")
    session_id = opened.cookies.get("phisim_session")
    assert session_id

    response = client.get(f"/inbox/{MESSAGE_ID}/link")
    assert response.status_code == 200
    assert "Techno Main Salt Lake" in response.text
    assert 'name="password"' in response.text


def test_attachment_open_is_inert_and_emits_event(
    client: TestClient,
    test_engine: Engine,
) -> None:
    opened = client.get(f"/inbox/{ATTACHMENT_MESSAGE_ID}")
    session_id = opened.cookies.get("phisim_session")
    assert session_id
    assert "Expense_Reimbursement_Form.pdf" in opened.text

    response = client.get(f"/inbox/{ATTACHMENT_MESSAGE_ID}/attachment")

    assert response.status_code == 200
    assert response.history
    assert response.history[0].status_code == 302
    assert (
        response.history[0]
        .headers["location"]
        .endswith(f"/inbox/{ATTACHMENT_MESSAGE_ID}")
    )

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == [
        "message_opened",
        "attachment_opened",
        "message_opened",
    ]
    attachment = events[1]
    assert attachment.scenario_id == ATTACHMENT_MESSAGE_ID
    assert attachment.metadata_ == {
        "channel": "email",
        "attachment_name": "Expense_Reimbursement_Form.pdf",
    }


def test_link_spoofing_displays_distinct_destination(
    client: TestClient,
) -> None:
    response = client.get("/inbox/link-spoof-001")

    assert response.status_code == 200
    assert "techno-main.edu/documents/shared" in response.text
    assert "/inbox/link-spoof-001/link" in response.text


def test_unknown_message_paths_return_404(client: TestClient) -> None:
    for path in (
        "/inbox/does-not-exist",
        "/inbox/does-not-exist/link",
        f"/inbox/{MESSAGE_ID}/link/extra",
    ):
        assert client.get(path).status_code == 404


def test_attachment_route_requires_attachment(client: TestClient) -> None:
    response = client.get(f"/inbox/{MESSAGE_ID}/attachment")
    assert response.status_code == 404
