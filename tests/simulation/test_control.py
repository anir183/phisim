from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.repos.event import EventRepository
from phisim.infra.sqlite.repos.simulation_run import SimulationRunRepository
from phisim.simulation.catalog import catalog_summaries
from phisim.simulation.control import TARGET_ROLE_CHOICES


def test_application_root_redirects_to_operator_lab(
    client: TestClient,
) -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/lab"


def test_lab_page_exposes_operator_workspace(client: TestClient) -> None:
    response = client.get("/lab")

    assert response.status_code == 200
    assert "Scenario Lab" in response.text
    assert "Gemail" in response.text
    assert "QuickChat" in response.text
    assert "Fictional target preset" in response.text
    assert "No external" in response.text or "external" in response.text
    assert "Recent local runs" in response.text


def test_every_catalog_target_role_is_launchable() -> None:
    missing = [
        summary.scenario_id
        for summary in catalog_summaries()
        if summary.target_role not in TARGET_ROLE_CHOICES
    ]

    assert missing == []


def test_support_portal_launch_accepts_its_fictional_target_role(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/lab/launch",
        json={
            "scenario_id": "support-portal-001",
            "target_role": "university employee",
            "delay_profile": "instant",
        },
    )

    assert response.status_code == 200
    assert response.json()["target_role"] == "university employee"
    assert response.json()["launch_path"] == "/scenario/support-portal-001"


def test_lab_api_filters_scenarios_without_exposing_arbitrary_targets(
    client: TestClient,
) -> None:
    response = client.get("/api/lab/scenarios", params={"channel": "email"})

    assert response.status_code == 200
    body = response.json()
    assert body
    assert {item["channel"] for item in body} == {"email"}
    assert all(item["scenario_id"] for item in body)
    assert all("real-person" not in str(item) for item in body)
    assert all(item["launch_path"].startswith("/") for item in body)


def test_lab_launch_creates_session_run_and_safe_start_event(
    client: TestClient,
    test_engine: Engine,
) -> None:
    response = client.post(
        "/api/lab/launch",
        json={
            "scenario_id": "email-phish-001",
            "target_role": "student",
            "delay_profile": "instant",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert response.content
    assert int(response.headers["content-length"]) > 0
    session_id = body["session_id"]
    assert body["run_id"]
    assert body["launch_path"] == "/inbox/email-phish-001"
    assert client.cookies.get("phisim_session") == session_id

    with Session(test_engine) as database_session:
        run = SimulationRunRepository(database_session).get_by_run_id(
            body["run_id"]
        )
        assert run is not None
        assert run.session_id == session_id
        assert run.scenario_id == "email-phish-001"
        assert run.state["last_action"] == "scenario_started"

        events = EventRepository(database_session).list_by_session(session_id)
        assert [event.event_type for event in events] == ["scenario_started"]
        assert events[0].metadata_["target_role"] == "student"
        assert events[0].metadata_["delay_profile"] == "instant"

    analysis = client.get(f"/api/analysis/sessions/{session_id}")
    assert analysis.status_code == 200
    assert analysis.json()["timeline"][0]["event_type"] == "scenario_started"


def test_lab_launch_rejects_unapproved_target_and_timing(
    client: TestClient,
) -> None:
    target_response = client.post(
        "/api/lab/launch",
        json={
            "scenario_id": "email-phish-001",
            "target_role": "real-person@example.com",
            "delay_profile": "instant",
        },
    )
    timing_response = client.post(
        "/api/lab/launch",
        json={
            "scenario_id": "email-phish-001",
            "target_role": "student",
            "delay_profile": "unbounded",
        },
    )

    assert target_response.status_code == 422
    assert timing_response.status_code == 422


def test_support_portal_html_launch_redirects_to_local_route(
    client: TestClient,
) -> None:
    response = client.post(
        "/lab/launch",
        data={
            "scenario_id": "support-portal-001",
            "target_role": "university employee",
            "delay_profile": "instant",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == (
        "/scenario/support-portal-001?delay=instant"
    )


def test_lab_html_launch_redirects_to_local_route(
    client: TestClient,
) -> None:
    response = client.post(
        "/lab/launch",
        data={
            "scenario_id": "sms-parcel-001",
            "target_role": "online shopper",
            "delay_profile": "instant",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/sms/sms-parcel-001?delay=instant"
    assert client.cookies.get("phisim_session")
