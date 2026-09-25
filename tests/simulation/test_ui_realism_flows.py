from datetime import UTC, datetime

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

    continued = client.post(
        f"{target}/continue",
        data={"identifier": "local-training-address"},
        follow_redirects=False,
    )
    assert continued.status_code == 303
    checkout = client.get(continued.headers["location"])
    assert checkout.status_code == 200
    assert "amazaun-checkout" in checkout.text

    finished = client.post(
        f"{target}/finish",
        data={"confirmation": "local-training-confirmation"},
        follow_redirects=False,
    )
    assert finished.status_code == 303
    debrief = client.get(finished.headers["location"])
    assert debrief.status_code == 200
    assert "What happened?" in debrief.text
    assert "training-reveal" in debrief.text


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

    finished = client.post(
        f"{target}/finish",
        data={"confirmation": "local-training-confirmation"},
        follow_redirects=False,
    )
    assert finished.status_code == 303
    debrief = client.get(finished.headers["location"])
    assert debrief.status_code == 200
    assert "training-reveal" in debrief.text


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
