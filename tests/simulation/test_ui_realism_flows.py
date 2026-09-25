from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

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


def _make_due(engine: Engine, attack_id: str) -> None:
    with Session(engine) as database_session:
        repository = SimulationAttackRepository(database_session)
        attack = repository.get_by_attack_id(attack_id)
        assert attack is not None
        attack.delivery_due_at = datetime.now(UTC)
        repository.save(attack)


def test_gemail_manual_route_has_mailbox_detail_and_state_flow(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "email-phish-001", "student")
    token = launch["victim_path"].split("/")[2]
    _make_due(test_engine, launch["attack_id"])

    inbox = client.get(f"/v/{token}/mail")
    assert inbox.status_code == 200
    assert "gmail-shell" in inbox.text
    assert "gmail-message-row" in inbox.text

    detail = client.get(
        f"/v/{token}/mail/email-phish-001",
        params={"delivery_id": launch["attack_id"]},
    )
    assert detail.status_code == 200
    assert "gmail-message-view" in detail.text
    assert "Open message link" in detail.text

    starred = client.post(
        f"/v/{token}/mail/email-phish-001/state",
        params={"delivery_id": launch["attack_id"], "folder": "inbox"},
        data={"action": "star"},
        follow_redirects=False,
    )
    assert starred.status_code == 303
    starred_inbox = client.get(
        f"/v/{token}/mail",
        params={"folder": "starred"},
    )
    assert "email-phish-001" in starred_inbox.text


def test_quickchat_manual_route_has_conversation_and_composer_flow(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "sms-parcel-001", "online shopper")
    token = launch["victim_path"].split("/")[2]
    _make_due(test_engine, launch["attack_id"])

    conversations = client.get(f"/v/{token}/messages")
    assert conversations.status_code == 200
    assert "quickchat-app" in conversations.text
    assert "quickchat-thread" in conversations.text

    conversation = client.get(
        f"/v/{token}/messages/sms-parcel-001",
        params={"delivery_id": launch["attack_id"]},
    )
    assert conversation.status_code == 200
    assert "quickchat-chat-panel" in conversation.text
    assert "Composer is read-only" in conversation.text

    search = client.get(f"/v/{token}/messages", params={"q": "parcel"})
    assert "sms-parcel-001" in search.text


def test_amazaun_manual_route_walks_order_to_debrief(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "credential-shopping-001", "online shopper")
    token = launch["victim_path"].split("/")[2]
    _make_due(test_engine, launch["attack_id"])
    target = f"/v/{token}/site/credential-shopping-001"

    order = client.get(target)
    assert order.status_code == 200
    assert "amazaun-app" in order.text
    assert "Order #1042-991" in order.text
    assert "Private training environment" not in order.text
    assert "Local security lab" not in order.text

    continued = client.post(
        f"{target}/continue",
        data={"identifier": "local-training-address"},
        follow_redirects=False,
    )
    assert continued.status_code == 303
    checkout = client.get(continued.headers["location"])
    assert checkout.status_code == 200
    assert "amazaun-checkout" in checkout.text
    assert "Payment method" in checkout.text
    assert "Delivery address" not in checkout.text
    assert 'name="payment_method"' in checkout.text

    finished = client.post(
        f"{target}/finish",
        data={"payment_method": "Fictional card ending 4242"},
        follow_redirects=False,
    )
    assert finished.status_code == 303
    destination = client.get(finished.headers["location"])
    assert destination.status_code == 200
    assert "Your order is confirmed" in destination.text
    assert "Fictional local training site" in destination.text
    assert "What happened?" not in destination.text
    status = client.get(f"/api/lab/attacks/{launch['attack_id']}")
    assert status.status_code == 200
    assert status.json()["status"] == "ENGAGED"
    assert status.json()["state"]["destination_reached"] is True
    assert status.json()["phase"] == "AWAITING_MANUAL_END"
    assert "attack_completed" not in [
        event["event_type"] for event in status.json()["events"]
    ]
    status_page = client.get(launch["operator_path"])
    assert status_page.status_code == 200
    assert "AWAITING_MANUAL_END" in status_page.text
    completed = client.post(f"{target}/end")
    assert completed.status_code == 200
    assert "What happened?" in completed.text
    assert "training-reveal" in completed.text


def test_cloudbox_manual_route_walks_shared_file_to_debrief(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "credential-cloud-001", "collaborator")
    token = launch["victim_path"].split("/")[2]
    _make_due(test_engine, launch["attack_id"])
    target = f"/v/{token}/site/credential-cloud-001"

    files = client.get(target)
    assert files.status_code == 200
    assert "cloudbox-app" in files.text
    assert "Shared with you" in files.text

    continued = client.post(
        f"{target}/continue",
        data={"identifier": "local-training-email"},
        follow_redirects=False,
    )
    assert continued.status_code == 303
    verification = client.get(continued.headers["location"])
    assert verification.status_code == 200
    assert "cloudbox-verify" in verification.text
    assert "Password" in verification.text
    assert 'name="password"' in verification.text
    assert "Work email" not in verification.text

    finished = client.post(
        f"{target}/finish",
        data={"password": "local-training-password"},
        follow_redirects=False,
    )
    assert finished.status_code == 303
    destination = client.get(finished.headers["location"])
    assert destination.status_code == 200
    assert "Your workspace is ready" in destination.text
    assert "What happened?" not in destination.text
    completed = client.post(f"{target}/end")
    assert completed.status_code == 200
    assert "training-reveal" in completed.text


@pytest.mark.parametrize(
    ("scenario_id", "role", "expected_heading", "expected_selector"),
    [
        (
            "credential-basic-001",
            "student",
            "Account access updated",
            "university-destination-calendar",
        ),
        (
            "credential-shopping-001",
            "online shopper",
            "Your order is confirmed",
            "amazaun-destination-products",
        ),
        (
            "credential-cloud-001",
            "collaborator",
            "Your workspace is ready",
            "cloudbox-destination-banner",
        ),
        (
            "credential-payment-001",
            "billing administrator",
            "Payment review recorded",
            "payment-destination-layout",
        ),
        (
            "support-portal-001",
            "university employee",
            "Case verification recorded",
            "support-ticket-list",
        ),
        (
            "mak-exam-001",
            "student",
            "Registration confirmed",
            "exam-destination-grid",
        ),
        (
            "technosphere-001",
            "faculty",
            "Course workspace unlocked",
            "course-destination-grid",
        ),
    ],
)
def test_each_product_flow_reaches_destination_before_manual_debrief(
    client: TestClient,
    test_engine: Engine,
    scenario_id: str,
    role: str,
    expected_heading: str,
    expected_selector: str,
) -> None:
    launch = _launch(client, scenario_id, role)
    token = launch["victim_path"].split("/")[2]
    _make_due(test_engine, launch["attack_id"])
    target = f"/v/{token}/site/{scenario_id}"

    landing = client.get(target)
    assert landing.status_code == 200
    continued = client.post(
        f"{target}/continue",
        data={"identifier": "local-training-identifier"},
        follow_redirects=False,
    )
    assert continued.status_code == 303
    if scenario_id == "credential-shopping-001":
        finish_data = {"payment_method": "Fictional card ending 4242"}
    elif scenario_id == "credential-cloud-001":
        finish_data = {"password": "local-training-password"}
    else:
        finish_data = {"confirmation": "local-training-confirmation"}
    finished = client.post(
        f"{target}/finish",
        data=finish_data,
        follow_redirects=False,
    )
    assert finished.status_code == 303
    destination = client.get(finished.headers["location"])
    assert destination.status_code == 200
    assert expected_heading in destination.text
    assert expected_selector in destination.text
    assert "End simulation" in destination.text
    assert "What happened?" not in destination.text

    completed = client.post(f"{target}/end")
    assert completed.status_code == 200
    assert "What happened?" in completed.text


def test_step_two_surfaces_keep_roomy_product_shells(
    client: TestClient,
    test_engine: Engine,
) -> None:
    cases = [
        ("credential-basic-001", "student", "university-auth"),
        ("credential-shopping-001", "online shopper", "amazaun-checkout"),
        ("credential-cloud-001", "collaborator", "cloudbox-verify"),
        ("credential-payment-001", "billing administrator", "payment-review"),
        ("support-portal-001", "university employee", "support-auth"),
        ("mak-exam-001", "student", "exam-auth"),
        ("technosphere-001", "faculty", "course-auth"),
    ]
    for scenario_id, role, expected_shell in cases:
        launch = _launch(client, scenario_id, role)
        token = launch["victim_path"].split("/")[2]
        _make_due(test_engine, launch["attack_id"])
        target = f"/v/{token}/site/{scenario_id}"
        continued = client.post(
            f"{target}/continue",
            data={"identifier": "local-training-identifier"},
            follow_redirects=False,
        )
        assert continued.status_code == 303
        step_two = client.get(continued.headers["location"])
        assert step_two.status_code == 200
        assert expected_shell in step_two.text
        assert "What happened?" not in step_two.text


def test_qr_manual_route_exposes_destination_before_local_scan(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "qr-phish-001", "student")
    token = launch["victim_path"].split("/")[2]
    _make_due(test_engine, launch["attack_id"])

    page = client.get(f"/v/{token}/qr/qr-phish-001")
    assert page.status_code == 200
    assert "qr-experience" in page.text
    assert "Destination preview" in page.text
    assert "data:image/png;base64," in page.text

    scanned = client.get(
        f"/v/{token}/qr/qr-phish-001/scan",
        follow_redirects=False,
    )
    assert scanned.status_code == 302
    destination = client.get(scanned.headers["location"])
    assert destination.status_code == 200
    assert "university-account" in destination.text
    target = f"/v/{token}/site/credential-basic-001"
    continued = client.post(
        f"{target}/continue",
        data={"identifier": "local-training-student"},
        follow_redirects=False,
    )
    assert continued.status_code == 303
    finished = client.post(
        f"{target}/finish",
        data={"password": "local-training-secret"},
        follow_redirects=False,
    )
    assert finished.status_code == 303
    result = client.get(finished.headers["location"])
    assert "Account access updated" in result.text
    assert "What happened?" not in result.text
    completed = client.post(f"{target}/end")
    assert completed.status_code == 200
    assert "What happened?" in completed.text


def test_legacy_email_handoff_uses_destination_before_manual_debrief(
    client: TestClient,
) -> None:
    opened = client.get("/inbox/email-phish-001")
    assert opened.status_code == 200
    link = client.get(
        "/inbox/email-phish-001/link",
        follow_redirects=False,
    )
    assert link.status_code == 302
    target = link.headers["location"].split("testserver", 1)[-1]
    continued = client.post(
        f"{target}/username",
        data={"username": "local-training-student"},
        follow_redirects=False,
    )
    assert continued.status_code == 303
    destination = client.post(
        f"{target}/password",
        data={"password": "local-training-secret"},
    )
    assert destination.status_code == 200
    assert "Account access updated" in destination.text
    assert "What happened?" not in destination.text
    completed = client.post(f"{target}/end")
    assert completed.status_code == 200
    assert "What happened?" in completed.text


def test_sms_handoff_reaches_product_destination_before_manual_debrief(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "sms-parcel-001", "online shopper")
    token = launch["victim_path"].split("/")[2]
    _make_due(test_engine, launch["attack_id"])
    link = client.get(
        f"/v/{token}/messages/sms-parcel-001/link",
        follow_redirects=False,
    )
    assert link.status_code == 302
    target = link.headers["location"]
    continued = client.post(
        f"{target}/continue",
        data={"identifier": "local-training-address"},
        follow_redirects=False,
    )
    assert continued.status_code == 303
    finished = client.post(
        f"{target}/finish",
        data={"confirmation": "local-training-confirmation"},
        follow_redirects=False,
    )
    assert finished.status_code == 303
    result = client.get(finished.headers["location"])
    assert "Your order is confirmed" in result.text
    assert "What happened?" not in result.text
    completed = client.post(f"{target}/end")
    assert completed.status_code == 200
    assert "What happened?" in completed.text


def test_mfa_manual_route_exposes_repeated_device_requests(
    client: TestClient,
    test_engine: Engine,
) -> None:
    launch = _launch(client, "mfa-fatigue-001", "student")
    token = launch["victim_path"].split("/")[2]
    _make_due(test_engine, launch["attack_id"])

    prompt = client.get(f"/v/{token}/mfa/mfa-fatigue-001/1")
    assert prompt.status_code == 200
    assert "nimbusid-device" in prompt.text
    assert "Request history" in prompt.text
    assert "Step 1 of 3" in prompt.text

    response = client.post(
        f"/v/{token}/mfa/mfa-fatigue-001/1",
        data={"action": "approve"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    next_prompt = client.get(response.headers["location"])
    assert "Step 2 of 3" in next_prompt.text
