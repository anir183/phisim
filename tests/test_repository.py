from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from phisim.infra.sqlite.connection import Base
from phisim.infra.sqlite.models.event import Event
from phisim.infra.sqlite.repos.event import EventRepository


def test_create_and_retrieve_event() -> None:
    engine = create_engine("sqlite://")

    Base.metadata.create_all(engine)

    with Session(engine) as session:
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
