from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.repos.simulation_attack import (
    SimulationAttackRepository,
)
from phisim.simulation.attack import SimulationAttackService


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


def _make_due(engine: Engine, attack_id: str) -> None:
    with Session(engine) as database_session:
        repository = SimulationAttackRepository(database_session)
        attack = repository.get_by_attack_id(attack_id)
        assert attack is not None
        attack.delivery_due_at = datetime.now(UTC)
        repository.save(attack)


def _complete(engine: Engine, attack_id: str) -> None:
    with Session(engine) as database_session:
        repository = SimulationAttackRepository(database_session)
        attack = repository.get_by_attack_id(attack_id)
        assert attack is not None
        service = SimulationAttackService(repository)
        if attack.status == "DELIVERED":
            service.transition(attack, "ENGAGED")
        if attack.status == "ENGAGED":
            service.transition(attack, "COMPLETED")


@pytest.mark.parametrize(
    ("scenario_id", "role", "artifact_id", "list_path", "detail_path"),
    [
        (
            "email-phish-001",
            "student",
            "email-phish-001",
            "mail",
            "mail/email-phish-001",
        ),
        (
            "sms-parcel-001",
            "online shopper",
            "sms-parcel-001",
            "messages",
            "messages/sms-parcel-001",
        ),
    ],
)
def test_terminal_attack_keeps_artifact_list_and_opens_read_only_details(
    client: TestClient,
    test_engine: Engine,
    scenario_id: str,
    role: str,
    artifact_id: str,
    list_path: str,
    detail_path: str,
) -> None:
    launch = _launch(client, scenario_id, role)
    token = launch["victim_path"].split("/")[2]
    _make_due(test_engine, launch["attack_id"])
    delivered_listing = client.get(f"/v/{token}/{list_path}")
    assert delivered_listing.status_code == 200
    assert artifact_id in delivered_listing.text
    _complete(test_engine, launch["attack_id"])

    listing = client.get(f"/v/{token}/{list_path}")
    assert listing.status_code == 200
    assert artifact_id in listing.text

    detail = client.get(
        f"/v/{token}/{detail_path}",
        params={"delivery_id": launch["attack_id"]},
    )
    assert detail.status_code == 200
    assert "read-only" in detail.text
    assert (
        "Action required: verify your mailbox" in detail.text
        or "Reply or confirm now" in detail.text
    )


def test_abandoned_attack_keeps_mail_and_conversation_lists_readable(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "email-phish-001", "student")
    token = launch["victim_path"].split("/")[2]
    _make_due(test_engine, launch["attack_id"])
    delivered = client.get(f"/v/{token}/mail")
    assert delivered.status_code == 200
    assert "email-phish-001" in delivered.text
    abandoned = client.post(f"/api/lab/attacks/{launch['attack_id']}/abandon")
    assert abandoned.status_code == 200

    mailbox = client.get(f"/v/{token}/mail")
    assert mailbox.status_code == 200
    assert "email-phish-001" in mailbox.text
    closed = client.get(
        f"/v/{token}/mail/email-phish-001",
        params={"delivery_id": launch["attack_id"]},
    )
    assert closed.status_code == 200
    assert "Action required: verify your mailbox" in closed.text
    assert "read-only" in closed.text


def test_quickchat_list_uses_last_message_and_clears_unread_after_open(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "sms-parcel-001", "online shopper")
    token = launch["victim_path"].split("/")[2]
    _make_due(test_engine, launch["attack_id"])

    inbox = client.get(f"/v/{token}/messages")
    assert inbox.status_code == 200
    assert "typing" not in inbox.text.lower()
    assert "Reply or confirm now" in inbox.text
    assert "UNREAD" in inbox.text

    opened = client.get(
        f"/v/{token}/messages/sms-parcel-001",
        params={"delivery_id": launch["attack_id"]},
    )
    assert opened.status_code == 200
    assert "typing" not in opened.text.lower()
    assert "Composer is read-only" in opened.text

    after_open = client.get(f"/v/{token}/messages")
    row_start = after_open.text.find('data-thread-id="sms-parcel-001"')
    row_end = after_open.text.find("</a>", row_start)
    assert "UNREAD" not in after_open.text[row_start:row_end]


def test_layout_regressions_keep_portal_chrome_and_light_lab_separate(
    client: TestClient,
    test_engine: Engine,
) -> None:
    account = _launch(client, "credential-basic-001", "student")
    account_token = account["victim_path"].split("/")[2]
    _make_due(test_engine, account["attack_id"])
    account_page = client.get(f"/v/{account_token}/site/credential-basic-001")
    alert_start = account_page.text.find('<section class="university-alert"')
    alert_end = account_page.text.find("</section>", alert_start)
    steps_start = account_page.text.find("university-alert-steps")
    assert alert_start >= 0
    assert alert_end > alert_start
    assert steps_start > alert_end

    course = _launch(client, "technosphere-001", "faculty")
    course_token = course["victim_path"].split("/")[2]
    _make_due(test_engine, course["attack_id"])
    course_page = client.get(f"/v/{course_token}/site/technosphere-001")
    assert 'class="course-nav"' in course_page.text
    assert 'class="course-access-icon"' in course_page.text

    lab = client.get("/lab")
    assert 'class="lab-body"' in lab.text
    assert 'class="operator-body console-body"' not in lab.text

    stylesheet = client.get("/static/phisim.css")
    assert ".gmail-star-action button:hover" in stylesheet.text
    assert ".nimbusid-actions .nimbusid-deny:hover" in stylesheet.text
    assert ".product-document" in stylesheet.text
    assert ".victim-product-main" in stylesheet.text
    assert ".legacy-shell.mock-site .page-frame" in stylesheet.text
    assert ".destination-main" in stylesheet.text

    console = client.get("/console")
    assert 'class="lab-body console-body"' in console.text
    assert ".console-body .operator-console-panel" in stylesheet.text
