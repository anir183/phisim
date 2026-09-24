import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("path", "scenario_id", "scenario_name", "scenario_type"),
    [
        (
            "/scenario/credential-basic-001",
            "credential-basic-001",
            "Mailbox Quota Exceeded Notice",
            "website",
        ),
        (
            "/inbox/email-phish-001",
            "email-phish-001",
            "Action required: verify your mailbox",
            "email",
        ),
        (
            "/sms/sms-parcel-001",
            "sms-parcel-001",
            "Techno Main Parcel",
            "sms",
        ),
        (
            "/qr/qr-phish-001",
            "qr-phish-001",
            "Verification Required",
            "qr",
        ),
        (
            "/mfa/mfa-fatigue-001/1",
            "mfa-fatigue-001",
            "Approve Sign-In",
            "mfa",
        ),
    ],
)
def test_catalog_entry_registers_shared_scenario_and_session(
    client: TestClient,
    path: str,
    scenario_id: str,
    scenario_name: str,
    scenario_type: str,
) -> None:
    response = client.get(path)

    assert response.status_code == 200
    session_id = response.cookies.get("phisim_session")
    assert session_id

    scenario_response = client.get(f"/api/scenarios/{scenario_id}")
    assert scenario_response.status_code == 200
    scenario = scenario_response.json()
    assert scenario["scenario_id"] == scenario_id
    assert scenario["name"] == scenario_name
    assert scenario["scenario_type"] == scenario_type
    assert scenario["description"]
    assert scenario["created_at"].endswith("Z")

    session_response = client.get(f"/api/sessions/{session_id}")
    assert session_response.status_code == 200
    assert session_response.json()["session_id"] == session_id
    assert session_response.json()["scenario_id"] == scenario_id
    assert session_response.json()["status"] == "active"


def test_website_submission_completes_shared_session(
    client: TestClient,
) -> None:
    opened = client.get("/scenario/credential-basic-001")
    session_id = opened.cookies.get("phisim_session")
    assert session_id

    submitted = client.post(
        "/scenario/credential-basic-001",
        data={"username": "student", "password": "not-stored"},
    )

    assert submitted.status_code == 200
    session_response = client.get(f"/api/sessions/{session_id}")
    assert session_response.status_code == 200
    assert session_response.json()["status"] == "completed"
    assert session_response.json()["completed_at"].endswith("Z")


def test_email_funnel_reuses_one_session_across_registered_scenarios(
    client: TestClient,
) -> None:
    opened = client.get("/inbox/email-phish-001")
    session_id = opened.cookies.get("phisim_session")
    assert session_id

    followed = client.get("/inbox/email-phish-001/link")

    assert followed.status_code == 200
    assert client.get("/api/scenarios/email-phish-001").status_code == 200
    assert client.get("/api/scenarios/credential-basic-001").status_code == 200
    sessions = client.get("/api/sessions")
    assert sessions.status_code == 200
    assert [item["session_id"] for item in sessions.json()] == [session_id]
    assert sessions.json()[0]["scenario_id"] == "email-phish-001"

    events = client.get(f"/api/events?session_id={session_id}")
    assert events.status_code == 200
    assert [item["event_type"] for item in events.json()] == [
        "message_opened",
        "link_clicked",
        "scenario_opened",
    ]


def test_terminal_mfa_response_completes_shared_session(
    client: TestClient,
) -> None:
    opened = client.get("/mfa/mfa-fatigue-001/1")
    session_id = opened.cookies.get("phisim_session")
    assert session_id

    denied = client.post(
        "/mfa/mfa-fatigue-001/1",
        data={"action": "deny"},
    )

    assert denied.status_code == 200
    session_response = client.get(f"/api/sessions/{session_id}")
    assert session_response.status_code == 200
    assert session_response.json()["status"] == "completed"
    assert session_response.json()["completed_at"].endswith("Z")
