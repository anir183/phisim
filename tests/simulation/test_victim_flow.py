from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.repos.event import EventRepository
from phisim.infra.sqlite.repos.session import SessionRepository
from phisim.infra.sqlite.repos.simulation_attack import (
    SimulationAttackRepository,
)


def _launch(client: TestClient, scenario_id: str, role: str) -> dict:
    response = client.post(
        "/api/lab/launch",
        json={
            "scenario_id": scenario_id,
            "target_role": role,
            "delay_profile": "short",
        },
    )
    assert response.status_code == 200
    return response.json()


def _set_due(engine: Engine, attack_id: str, due: datetime) -> None:
    with Session(engine) as database_session:
        repository = SimulationAttackRepository(database_session)
        attack = repository.get_by_attack_id(attack_id)
        assert attack is not None
        attack.delivery_due_at = due
        repository.save(attack)


def test_preopened_mailbox_is_the_environment_used_by_operator_launch(
    client: TestClient,
    test_engine: Engine,
) -> None:
    baseline = client.get("/mail")
    assert baseline.status_code == 200
    assert "ordinary-001" in baseline.text
    assert "email-phish-001" not in baseline.text
    assert "Scenario Lab" not in baseline.text
    token = client.cookies.get("phisim_victim_context")
    assert token
    assert client.get(f"/v/{token}/mail/ordinary-001").status_code == 200
    assert (
        client.get(f"/v/{token}/messages/ordinary-sms-001").status_code == 200
    )

    launch = _launch(client, "email-phish-001", "student")
    assert launch["victim_path"] == f"/v/{token}/mail"
    _set_due(
        test_engine,
        launch["attack_id"],
        datetime.now(UTC) + timedelta(hours=1),
    )
    still_baseline = client.get("/mail")
    assert "email-phish-001" not in still_baseline.text
    _set_due(
        test_engine,
        launch["attack_id"],
        datetime.now(UTC) - timedelta(seconds=1),
    )
    delivered = client.get("/mail")
    assert "email-phish-001" in delivered.text


def test_operator_launch_keeps_attack_separate_until_victim_delivery(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "email-phish-001", "student")
    token = launch["victim_path"].split("/")[2]

    _set_due(
        test_engine,
        launch["attack_id"],
        datetime.now(UTC) + timedelta(hours=1),
    )
    before = client.get(f"/v/{token}/mail")
    assert before.status_code == 200
    early_target = client.get(f"/v/{token}/site/credential-basic-001")
    assert early_target.status_code == 404
    assert "ordinary-001" in before.text
    assert "email-phish-001" not in before.text
    assert "Scenario Lab" not in before.text

    _set_due(
        test_engine,
        launch["attack_id"],
        datetime.now(UTC) - timedelta(seconds=1),
    )
    status = client.get(f"/v/{token}/status")
    assert status.status_code == 200
    assert status.json()["status"] == "DELIVERED"
    assert "email-phish-001" in status.json()["state"]["delivered_message_ids"]

    delivered = client.get(f"/v/{token}/mail")
    assert "email-phish-001" in delivered.text

    with Session(test_engine) as database_session:
        attack = SimulationAttackRepository(database_session).get_by_attack_id(
            launch["attack_id"]
        )
        assert attack is not None
        assert attack.victim_session_id != attack.operator_session_id
        events = EventRepository(database_session).list_by_session(
            attack.operator_session_id
        )
        assert "message_delivered" in [event.event_type for event in events]


def test_victim_email_link_site_and_safe_completion_are_one_session(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "email-phish-001", "student")
    token = launch["victim_path"].split("/")[2]
    _set_due(test_engine, launch["attack_id"], datetime.now(UTC))

    opened = client.get(f"/v/{token}/mail/email-phish-001")
    assert opened.status_code == 200
    link = client.get(
        f"/v/{token}/mail/email-phish-001/link",
        follow_redirects=False,
    )
    assert link.status_code == 302
    site_path = link.headers["location"]
    site = client.get(site_path)
    assert site.status_code == 200
    continued = client.post(
        f"{site_path}/continue",
        data={"identifier": "fictional-student"},
        follow_redirects=False,
    )
    assert continued.status_code == 303
    processing = client.post(
        f"{site_path}/finish",
        data={"password": "fictional-secret"},
        follow_redirects=False,
    )
    assert processing.status_code == 303
    assert processing.headers["location"].endswith("/result")
    result = client.get(processing.headers["location"])
    assert result.status_code == 200
    assert "Checking your request" in result.text
    completed = client.post(processing.headers["location"])
    assert completed.status_code == 200
    assert "What happened?" in completed.text
    assert "fictional-secret" not in completed.text
    assert "/simulation" not in completed.text
    final_status = client.get(f"/v/{token}/status")
    assert final_status.status_code == 200
    assert final_status.json()["status"] == "COMPLETED"

    with Session(test_engine) as database_session:
        attack = SimulationAttackRepository(database_session).get_by_attack_id(
            launch["attack_id"]
        )
        assert attack is not None
        assert attack.status == "COMPLETED"
        events = EventRepository(database_session).list_by_session(
            attack.operator_session_id
        )
        event_types = [event.event_type for event in events]
        assert event_types == [
            "scenario_started",
            "attack_armed",
            "message_delivered",
            "message_opened",
            "link_clicked",
            "website_viewed",
            "credential_submission_attempted",
            "processing_started",
            "attack_completed",
            "scenario_completed",
        ]
        assert "fictional-secret" not in str(
            [event.metadata_ for event in events]
        )
        victim_session = SessionRepository(database_session).get_by_session_id(
            attack.victim_session_id
        )
        assert victim_session is not None
        assert victim_session.status == "completed"

    analysis = client.get(f"/api/analysis/sessions/{launch['session_id']}")
    assert analysis.status_code == 200
    timeline = analysis.json()["timeline"]
    assert "message_delivered" in [entry["event_type"] for entry in timeline]
    assert "processing_started" in [entry["event_type"] for entry in timeline]
    delivery_entry = next(
        entry
        for entry in timeline
        if entry["event_type"] == "message_delivered"
    )
    assert "available" in delivery_entry["description"]


def test_attachment_preview_is_delivered_and_inert(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "attachment-phish-001", "collaborator")
    token = launch["victim_path"].split("/")[2]
    _set_due(test_engine, launch["attack_id"], datetime.now(UTC))

    email = client.get(f"/v/{token}/mail/attachment-phish-001")
    assert email.status_code == 200
    assert "Preview attachment" in email.text
    attachment = client.get(f"/v/{token}/mail/attachment-phish-001/attachment")
    assert attachment.status_code == 200
    assert "No download" in attachment.text
    assert "Expense_Reimbursement_Form.pdf" in attachment.text


def test_qr_flow_uses_a_distinct_scan_mechanism(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "qr-phish-001", "student")
    token = launch["victim_path"].split("/")[2]
    _set_due(test_engine, launch["attack_id"], datetime.now(UTC))

    page = client.get(f"/v/{token}/qr/qr-phish-001")
    assert page.status_code == 200
    assert "Simulate scan" in page.text
    scan = client.get(
        f"/v/{token}/qr/qr-phish-001/scan",
        follow_redirects=False,
    )
    assert scan.status_code == 302
    assert "/site/credential-basic-001" in scan.headers["location"]
    with Session(test_engine) as database_session:
        attack = SimulationAttackRepository(database_session).get_by_attack_id(
            launch["attack_id"]
        )
        assert attack is not None
        events = EventRepository(database_session).list_by_session(
            attack.operator_session_id
        )
        assert "qr_scan_simulated" in [event.event_type for event in events]


def test_mfa_flow_repeats_prompts_before_completion(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "mfa-fatigue-001", "student")
    token = launch["victim_path"].split("/")[2]
    _set_due(test_engine, launch["attack_id"], datetime.now(UTC))

    for step in (1, 2, 3):
        page = client.get(f"/v/{token}/mfa/mfa-fatigue-001/{step}")
        assert page.status_code == 200
        response = client.post(
            f"/v/{token}/mfa/mfa-fatigue-001/{step}",
            data={"action": "approve"},
            follow_redirects=False,
        )
        if step < 3:
            assert response.status_code == 303
        else:
            assert response.status_code == 200
            assert "What happened?" in response.text

    with Session(test_engine) as database_session:
        attack = SimulationAttackRepository(database_session).get_by_attack_id(
            launch["attack_id"]
        )
        assert attack is not None
        assert attack.status == "COMPLETED"
        events = EventRepository(database_session).list_by_session(
            attack.operator_session_id
        )
        event_types = [event.event_type for event in events]
        assert event_types.count("mfa_prompt_displayed") == 3
        assert event_types.count("mfa_prompt_responded") == 3
        assert event_types[-2:] == ["attack_completed", "scenario_completed"]


def test_academic_portals_have_distinct_fictional_workflows(
    client: TestClient,
    test_engine: Engine,
) -> None:
    exam = _launch(client, "mak-exam-001", "student")
    _set_due(test_engine, exam["attack_id"], datetime.now(UTC))
    exam_page = client.get(exam["victim_path"])
    assert exam_page.status_code == 200
    assert "MAKExam" in exam_page.text
    assert "Exam registration ID" in exam_page.text

    learning = _launch(client, "technosphere-001", "faculty")
    _set_due(test_engine, learning["attack_id"], datetime.now(UTC))
    learning_page = client.get(learning["victim_path"])
    assert learning_page.status_code == 200
    assert "TechnoSphere" in learning_page.text
    assert "Course code" in learning_page.text


def test_shopping_flow_uses_confirmation_instead_of_password(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "credential-shopping-001", "online shopper")
    _set_due(test_engine, launch["attack_id"], datetime.now(UTC))
    site_path = launch["victim_path"]
    continued = client.post(
        f"{site_path}/continue",
        data={"identifier": "fictional-shopper"},
        follow_redirects=False,
    )
    assert continued.status_code == 303
    processing = client.post(
        f"{site_path}/finish",
        data={"confirmation": "12 Example Street"},
        follow_redirects=False,
    )
    assert processing.status_code == 303
    result = client.get(processing.headers["location"])
    assert result.status_code == 200
    completed = client.post(processing.headers["location"])
    assert completed.status_code == 200
    assert "What happened?" in completed.text

    with Session(test_engine) as database_session:
        attack = SimulationAttackRepository(database_session).get_by_attack_id(
            launch["attack_id"]
        )
        assert attack is not None
        events = EventRepository(database_session).list_by_session(
            attack.operator_session_id
        )
        event_types = [event.event_type for event in events]
        assert "victim_action_completed" in event_types
        assert "credential_submission_attempted" not in event_types


def test_preopened_quickchat_receives_only_the_launched_thread(
    client: TestClient,
    test_engine: Engine,
) -> None:
    baseline = client.get("/messages")
    assert baseline.status_code == 200
    assert "ordinary-sms-001" in baseline.text
    assert "sms-parcel-001" not in baseline.text
    token = client.cookies.get("phisim_victim_context")
    assert token

    launch = _launch(client, "sms-parcel-001", "online shopper")
    assert launch["victim_path"] == f"/v/{token}/messages"
    _set_due(test_engine, launch["attack_id"], datetime.now(UTC))
    delivered = client.get("/messages")
    assert "ordinary-sms-001" in delivered.text
    assert "sms-parcel-001" in delivered.text


def test_sms_delivery_uses_the_same_attack_context(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "sms-parcel-001", "online shopper")
    token = launch["victim_path"].split("/")[2]
    _set_due(test_engine, launch["attack_id"], datetime.now(UTC))

    inbox = client.get(f"/v/{token}/messages")
    assert inbox.status_code == 200
    assert "ordinary-sms-001" in inbox.text
    assert "sms-parcel-001" in inbox.text

    opened = client.get(f"/v/{token}/messages/sms-parcel-001")
    assert opened.status_code == 200
    link = client.get(
        f"/v/{token}/messages/sms-parcel-001/link",
        follow_redirects=False,
    )
    assert link.status_code == 302
    site = client.get(link.headers["location"])
    assert site.status_code == 200
    assert "Amazaun" in site.text
