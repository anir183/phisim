from datetime import UTC, datetime

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from phisim.infra.sqlite.models.event import Event
from phisim.infra.sqlite.models.scenario import Scenario
from phisim.infra.sqlite.models.session import Session as SessionModel
from phisim.infra.sqlite.repos.event import EventRepository
from phisim.infra.sqlite.repos.scenario import ScenarioRepository
from phisim.infra.sqlite.repos.session import SessionRepository


def test_create_and_retrieve_event(test_engine: Engine) -> None:
    with Session(test_engine) as session:
        repository = EventRepository(session)

        event = Event(
            event_id="event-001",
            timestamp=datetime.now(UTC),
            session_id="session-001",
            scenario_id="scenario-001",
            event_type="page_viewed",
            source="browser",
            metadata_={"page": "/scenario/scenario-001"},
        )

        created = repository.create(event)

        assert created.id is not None
        assert created.event_id == "event-001"

        retrieved = repository.get_by_event_id("event-001")

        assert retrieved is not None
        assert retrieved.event_id == "event-001"
        assert retrieved.metadata_["page"] == "/scenario/scenario-001"


def test_create_and_retrieve_scenario(test_engine: Engine) -> None:
    with Session(test_engine) as session:
        repository = ScenarioRepository(session)
        created_at = datetime.now(UTC)
        scenario = Scenario(
            scenario_id="scenario-001",
            name="Example Scenario",
            scenario_type="credential",
            description="A local fictional scenario.",
            created_at=created_at,
        )

        created = repository.create(scenario)
        retrieved = repository.get_by_scenario_id("scenario-001")

        assert created.id is not None
        assert retrieved is not None
        assert retrieved.name == "Example Scenario"
        assert repository.list_all() == [retrieved]


def test_create_update_and_retrieve_session(test_engine: Engine) -> None:
    with Session(test_engine) as session:
        scenario_repository = ScenarioRepository(session)
        repository = SessionRepository(session)
        started_at = datetime.now(UTC)
        scenario = Scenario(
            scenario_id="scenario-001",
            name="Example Scenario",
            scenario_type="credential",
            description="",
            created_at=started_at,
        )
        scenario_repository.create(scenario)
        simulation_session = SessionModel(
            session_id="session-001",
            scenario_id="scenario-001",
            started_at=started_at,
            completed_at=None,
            status="active",
        )

        created = repository.create(simulation_session)
        created.status = "completed"
        created.completed_at = datetime.now(UTC)
        saved = repository.save(created)
        retrieved = repository.get_by_session_id("session-001")

        assert retrieved is not None
        assert retrieved.status == "completed"
        assert retrieved.completed_at is not None
        assert repository.list_all() == [saved]


def test_scenario_repository_rolls_back_duplicate(test_engine: Engine) -> None:
    with Session(test_engine) as session:
        repository = ScenarioRepository(session)
        created_at = datetime.now(UTC)
        repository.create(
            Scenario(
                scenario_id="scenario-duplicate",
                name="First Scenario",
                scenario_type="credential",
                description="",
                created_at=created_at,
            )
        )

        with pytest.raises(IntegrityError):
            repository.create(
                Scenario(
                    scenario_id="scenario-duplicate",
                    name="Second Scenario",
                    scenario_type="credential",
                    description="",
                    created_at=created_at,
                )
            )

        retrieved = repository.get_by_scenario_id("scenario-duplicate")

        assert retrieved is not None
        assert retrieved.name == "First Scenario"


def test_session_repository_rolls_back_duplicate(test_engine: Engine) -> None:
    with Session(test_engine) as session:
        scenario_repository = ScenarioRepository(session)
        repository = SessionRepository(session)
        started_at = datetime.now(UTC)
        scenario_repository.create(
            Scenario(
                scenario_id="scenario-duplicate",
                name="Scenario",
                scenario_type="credential",
                description="",
                created_at=started_at,
            )
        )
        repository.create(
            SessionModel(
                session_id="session-duplicate",
                scenario_id="scenario-duplicate",
                started_at=started_at,
                completed_at=None,
                status="active",
            )
        )

        with pytest.raises(IntegrityError):
            repository.create(
                SessionModel(
                    session_id="session-duplicate",
                    scenario_id="scenario-duplicate",
                    started_at=started_at,
                    completed_at=None,
                    status="completed",
                )
            )

        retrieved = repository.get_by_session_id("session-duplicate")

        assert retrieved is not None
        assert retrieved.status == "active"


def test_event_repository_rolls_back_duplicate(test_engine: Engine) -> None:
    with Session(test_engine) as session:
        repository = EventRepository(session)
        timestamp = datetime.now(UTC)
        repository.create(
            Event(
                event_id="event-duplicate",
                timestamp=timestamp,
                session_id="session-001",
                scenario_id="scenario-001",
                event_type="scenario_opened",
                source="browser",
                metadata_={},
            )
        )

        with pytest.raises(IntegrityError):
            repository.create(
                Event(
                    event_id="event-duplicate",
                    timestamp=timestamp,
                    session_id="session-001",
                    scenario_id="scenario-001",
                    event_type="scenario_interaction",
                    source="browser",
                    metadata_={},
                )
            )

        retrieved = repository.get_by_event_id("event-duplicate")

        assert retrieved is not None
        assert retrieved.event_type == "scenario_opened"
