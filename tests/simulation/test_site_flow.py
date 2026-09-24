import json

from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.models.event import Event
from phisim.infra.sqlite.repos.event import EventRepository

SCENARIO_ID = "credential-basic-001"


def _list_events(engine: Engine, session_id: str) -> list[Event]:
    with Session(engine) as session:
        repository = EventRepository(session)
        return repository.list_by_session(session_id)


def _open_session(client: TestClient) -> str:
    response = client.get(f"/scenario/{SCENARIO_ID}")
    assert response.status_code == 200
    session_id = response.cookies.get("phisim_session")
    assert session_id
    return session_id


def test_legacy_simulation_index_redirects_to_scenario_lab(
    client: TestClient,
) -> None:
    response = client.get("/simulation", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/lab"
    lab = client.get("/lab")
    assert lab.status_code == 200
    assert "Scenario Lab" in lab.text
    assert "Simulations" not in lab.text


def test_login_page_renders_and_assigns_session(
    client: TestClient,
    test_engine: Engine,
) -> None:
    response = client.get(f"/scenario/{SCENARIO_ID}")

    assert response.status_code == 200
    assert 'name="username"' in response.text
    assert response.text.count('class="step-label"') == 2
    assert response.text.count('class="step-dot"') == 2
    assert "password" not in response.text
    assert "UniSecure" in response.text

    session_id = response.cookies.get("phisim_session")
    assert session_id

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == ["scenario_opened"]
    assert events[0].scenario_id == SCENARIO_ID
    assert events[0].source == "browser"


def test_legacy_website_pages_use_the_shared_visual_themes(
    client: TestClient,
) -> None:
    cases = (
        ("credential-basic-001", "unisecure", "Northstar account center"),
        ("credential-shopping-001", "amazaun", "Your order is ready"),
        ("credential-cloud-001", "cloudbox", "Your CloudBox workspace"),
        ("credential-payment-001", "paymate", "Payment review center"),
        ("support-portal-001", "support", "Northstar IT support desk"),
        ("mak-exam-001", "makexam", "Assessment registration"),
        ("technosphere-001", "technosphere", "Course workspace"),
    )
    for scenario_id, theme_key, hero_text in cases:
        response = client.get(f"/scenario/{scenario_id}")
        assert response.status_code == 200
        assert f"mock-landing-{theme_key}" in response.text
        assert hero_text in response.text
        assert "End simulation" in response.text


def test_legacy_end_simulation_is_safe_and_idempotent(
    client: TestClient,
    test_engine: Engine,
) -> None:
    opened = client.get(f"/scenario/{SCENARIO_ID}")
    session_id = opened.cookies.get("phisim_session")
    assert session_id

    ended = client.post(f"/scenario/{SCENARIO_ID}/end")
    assert ended.status_code == 200
    assert "You ended the simulation safely" in ended.text
    assert "fictional-secret" not in ended.text

    repeated = client.post(f"/scenario/{SCENARIO_ID}/end")
    assert repeated.status_code == 200
    assert "You ended the simulation safely" in repeated.text

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == [
        "scenario_opened",
        "scenario_completed",
    ]
    assert events[1].metadata_["outcome"] == "ended_by_user"


def test_two_step_website_flow_keeps_credentials_out_of_state(
    client: TestClient,
    test_engine: Engine,
) -> None:
    opened = client.get(f"/scenario/{SCENARIO_ID}")
    session_id = opened.cookies.get("phisim_session")
    assert session_id

    username_step = client.post(
        f"/scenario/{SCENARIO_ID}/username",
        data={"username": "fictional-student"},
        follow_redirects=False,
    )
    assert username_step.status_code == 303
    assert username_step.headers["location"].endswith("/password")

    password_page = client.get(f"/scenario/{SCENARIO_ID}/password")
    assert password_page.status_code == 200
    assert 'name="password"' in password_page.text

    secret = "two-step-secret"
    completed = client.post(
        f"/scenario/{SCENARIO_ID}/password",
        data={"password": secret},
    )
    assert completed.status_code == 200
    assert secret not in completed.text
    assert "training outcome" in completed.text

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == [
        "scenario_opened",
        "credential_submission_attempted",
        "scenario_completed",
    ]
    submission = events[1]
    assert submission.metadata_["field_presence"] == {
        "username": True,
        "password": True,
    }
    assert secret not in json.dumps([event.metadata_ for event in events])


def test_unknown_or_traversal_scenario_returns_404(
    client: TestClient,
) -> None:
    for path in (
        "/scenario/does-not-exist",
        "/scenario/../../etc/passwd",
        "/scenario/credential-basic-001/extra",
    ):
        assert client.get(path).status_code == 404
        assert (
            client.post(
                path,
                data={"username": "a", "password": "b"},
            ).status_code
            == 404
        )


def test_malformed_session_cookie_is_replaced(client: TestClient) -> None:
    client.cookies.set("phisim_session", "../../etc/passwd")
    response = client.get(f"/scenario/{SCENARIO_ID}")

    assert response.status_code == 200
    session_id = response.cookies.get("phisim_session")
    assert session_id
    assert session_id != "../../etc/passwd"
    assert set(session_id) <= set("0123456789abcdef")


def test_credential_submission_emits_safe_event(
    client: TestClient,
    test_engine: Engine,
) -> None:
    session_id = _open_session(client)

    response = client.post(
        f"/scenario/{SCENARIO_ID}",
        data={"username": "student-42", "password": "hunter2"},
    )

    assert response.status_code == 200
    assert "training outcome" in response.text
    assert "hunter2" not in response.text
    assert "student-42" not in response.text

    events = _list_events(test_engine, session_id)
    assert [event.event_type for event in events] == [
        "scenario_opened",
        "credential_submission_attempted",
        "scenario_completed",
    ]

    submission = next(
        event
        for event in events
        if event.event_type == "credential_submission_attempted"
    )
    assert submission.session_id == session_id
    assert submission.scenario_id == SCENARIO_ID
    assert submission.source == "browser"
    assert submission.metadata_ == {
        "channel": "website",
        "interaction_result": "submitted",
        "field_presence": {"username": True, "password": True},
    }


def test_submitted_password_never_enters_any_event_field(
    client: TestClient,
    test_engine: Engine,
) -> None:
    session_id = _open_session(client)
    secret = "hunter2-super-secret"

    response = client.post(
        f"/scenario/{SCENARIO_ID}",
        data={"username": "anyone", "password": secret},
    )

    assert response.status_code == 200

    for event in _list_events(test_engine, session_id):
        payload = json.dumps(
            {
                "event_id": event.event_id,
                "session_id": event.session_id,
                "scenario_id": event.scenario_id,
                "event_type": event.event_type,
                "source": event.source,
                "metadata": event.metadata_,
            }
        )
        assert secret not in payload
        assert "password" not in event.metadata_
        assert "username" not in event.metadata_


def test_missing_fields_produce_incomplete_event(
    client: TestClient,
    test_engine: Engine,
) -> None:
    session_id = _open_session(client)

    response = client.post(f"/scenario/{SCENARIO_ID}", data={})

    assert response.status_code == 200

    events = _list_events(test_engine, session_id)
    submission = next(
        event
        for event in events
        if event.event_type == "credential_submission_attempted"
    )
    assert submission.metadata_["interaction_result"] == "incomplete"
    assert submission.metadata_["field_presence"] == {
        "username": False,
        "password": False,
    }


def test_submission_event_is_broadcast_over_websocket(
    client: TestClient,
) -> None:
    _open_session(client)

    with client.websocket_connect("/api/events/ws") as websocket:
        response = client.post(
            f"/scenario/{SCENARIO_ID}",
            data={"username": "wsuser", "password": "LetMeIn42!"},
        )
        assert response.status_code == 200

        payload = websocket.receive_json()

    assert payload["event_type"] == "credential_submission_attempted"
    assert payload["scenario_id"] == SCENARIO_ID
    assert payload["source"] == "browser"
    assert "LetMeIn42!" not in json.dumps(payload)
    assert "password" not in payload["metadata"]
