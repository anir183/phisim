from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.repos.sandbox_capture import SandboxCaptureRepository
from phisim.infra.sqlite.repos.simulation_attack import (
    SimulationAttackRepository,
)
from phisim.simulation.capture import clear_sandbox_capture_memory


def _launch(
    client: TestClient, scenario_id: str = "credential-basic-001"
) -> dict:
    response = client.post(
        "/api/lab/launch",
        json={
            "scenario_id": scenario_id,
            "target_role": "student",
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


def test_synthetic_capture_is_visible_in_reveal_and_console_api(
    client: TestClient,
    test_engine: Engine,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "phisim.simulation.capture.settings.sandbox_capture", True
    )
    clear_sandbox_capture_memory()
    launch = _launch(client)
    token = launch["victim_path"].split("/")[2]
    _make_due(test_engine, launch["attack_id"])
    target = f"/v/{token}/site/credential-basic-001"

    continued = client.post(
        f"{target}/continue",
        data={"identifier": "student@example.com"},
        follow_redirects=False,
    )
    assert continued.status_code == 303
    finished = client.post(
        f"{target}/finish",
        data={"password": "test-pass"},
        follow_redirects=False,
    )
    assert finished.status_code == 303
    completed = client.post(f"{target}/end")

    assert completed.status_code == 200
    assert "SYNTHETIC SANDBOX CAPTURE" in completed.text
    assert "student@example.com" in completed.text
    assert "test-pass" in completed.text
    evidence_index = completed.text.index("Evidence captured")
    capture_index = completed.text.index("SYNTHETIC SANDBOX CAPTURE")
    left_column_end = completed.text.index("</main>")
    assert left_column_end < capture_index
    assert evidence_index < capture_index

    response = client.get(
        "/api/sandbox/captures",
        params={"session_id": launch["session_id"]},
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["enabled"] is True
    fields = [
        field
        for capture in response.json()["captures"]
        for field in capture["fields"]
    ]
    assert {field["name"] for field in fields} == {"identifier", "password"}
    assert {field["value"] for field in fields} == {
        "student@example.com",
        "test-pass",
    }

    with Session(test_engine) as database_session:
        records = SandboxCaptureRepository(database_session).list_by_session(
            launch["session_id"]
        )
        assert len(records) == 2
        assert records[0].values == {"identifier": "student@example.com"}
        assert records[1].values == {}
        assert "test-pass" not in str(records[1].secret_digests)
        assert (
            records[1].secret_digests["password"].startswith("pbkdf2_sha256$")
        )


def test_invalid_email_and_secret_show_a_rejection_toast_without_advancing(
    client: TestClient,
    test_engine: Engine,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "phisim.simulation.capture.settings.sandbox_capture", True
    )
    clear_sandbox_capture_memory()
    launch = _launch(client)
    token = launch["victim_path"].split("/")[2]
    _make_due(test_engine, launch["attack_id"])
    target = f"/v/{token}/site/credential-basic-001"

    rejected_email = client.post(
        f"{target}/continue",
        data={"identifier": "student@gmail.com"},
    )
    assert rejected_email.status_code == 422
    assert "data-capture-error=" in rejected_email.text
    assert "@example.com or @gemail.com" in rejected_email.text
    assert "destination_reached" not in rejected_email.text

    accepted = client.post(
        f"{target}/continue",
        data={"identifier": "student@example.com"},
        follow_redirects=False,
    )
    assert accepted.status_code == 303
    rejected_secret = client.post(
        f"{target}/finish",
        data={"password": "real-looking-password"},
    )
    assert rejected_secret.status_code == 422
    assert "training-only value" in rejected_secret.text
    assert client.get(f"{target}?step=1").status_code == 200


def test_console_exposes_the_capture_endpoint_and_safe_dom_rendering(
    client: TestClient,
) -> None:
    page = client.get("/console")
    script = client.get("/static/console.js")

    assert page.status_code == 200
    assert "Synthetic sandbox values" in page.text
    assert "beside the matching Event" in page.text
    assert script.status_code == 200
    assert "/api/sandbox/captures" in script.text
    assert "innerHTML" not in script.text
    assert "renderSandboxCaptures" in script.text
    assert "renderEventCapture" in script.text
    assert "credential_submission_attempted" in script.text
