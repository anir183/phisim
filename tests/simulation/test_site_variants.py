import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.repos.event import EventRepository

SITE_CASES = [
    ("credential-basic-001", "UniSecure"),
    ("credential-shopping-001", "Amazaun"),
    ("credential-cloud-001", "CloudBox"),
    ("credential-payment-001", "PayMate"),
    ("support-portal-001", "UniSecure Support"),
    ("mak-exam-001", "MAKExam"),
    ("technosphere-001", "TechnoSphere"),
]


@pytest.mark.parametrize(("scenario_id", "brand"), SITE_CASES)
def test_each_parody_site_has_distinct_safe_shell(
    client: TestClient,
    scenario_id: str,
    brand: str,
) -> None:
    response = client.get(f"/scenario/{scenario_id}")

    assert response.status_code == 200
    assert brand in response.text
    assert "password" not in response.text
    assert ".example" in response.text
    assert "innerHTML" not in response.text


def test_each_parody_site_can_complete_two_step_training(
    client: TestClient,
    test_engine: Engine,
) -> None:
    session_ids: list[str] = []
    for scenario_id, _brand in SITE_CASES:
        username_step = client.post(
            f"/scenario/{scenario_id}/username",
            data={"username": "fictional-user"},
            follow_redirects=False,
        )
        assert username_step.status_code == 303
        session_id = client.cookies.get("phisim_session")
        assert session_id
        session_ids.append(session_id)
        password_step = client.post(
            f"/scenario/{scenario_id}/password",
            data={"password": "fictional-secret"},
        )
        assert password_step.status_code == 200
        assert "fictional-secret" not in password_step.text

    with Session(test_engine) as database_session:
        events = [
            event
            for session_id in set(session_ids)
            for event in EventRepository(database_session).list_by_session(
                session_id
            )
        ]
        assert [event.event_type for event in events].count(
            "credential_submission_attempted"
        ) == len(SITE_CASES)
        assert [event.event_type for event in events].count(
            "destination_reached"
        ) == len(SITE_CASES)
        assert all(
            "fictional-secret" not in str(event.metadata_) for event in events
        )
