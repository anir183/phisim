import asyncio
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
from phisim.scenarios.schemas import ScenarioCreate
from phisim.scenarios.service import DuplicateScenarioError, ScenarioService
from phisim.sessions.schemas import SessionCreate
from phisim.sessions.service import DuplicateSessionError, SessionService
from phisim.telemetry.schemas import EventCreate
from phisim.telemetry.service import DuplicateEventError, TelemetryService
from phisim.telemetry.websocket import EventConnectionManager


def test_scenario_service_maps_unique_race_to_duplicate(
    test_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with Session(test_engine) as database_session:
        repository = ScenarioRepository(database_session)
        existing = Scenario(
            scenario_id="scenario-race",
            name="Existing Scenario",
            scenario_type="credential",
            description="",
            created_at=datetime.now(UTC),
        )
        lookups = iter([None, existing])
        monkeypatch.setattr(
            repository,
            "get_by_scenario_id",
            lambda _scenario_id: next(lookups),
        )

        def fail_create(_scenario: Scenario) -> Scenario:
            raise IntegrityError("INSERT", {}, Exception("duplicate"))

        monkeypatch.setattr(repository, "create", fail_create)
        service = ScenarioService(repository)

        with pytest.raises(DuplicateScenarioError):
            service.create(
                ScenarioCreate(
                    scenario_id="scenario-race",
                    name="Racing Scenario",
                    scenario_type="credential",
                )
            )


def test_session_service_maps_unique_race_to_duplicate(
    test_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with Session(test_engine) as database_session:
        scenario_repository = ScenarioRepository(database_session)
        repository = SessionRepository(database_session)
        started_at = datetime.now(UTC)
        scenario_repository.create(
            Scenario(
                scenario_id="scenario-race",
                name="Scenario",
                scenario_type="credential",
                description="",
                created_at=started_at,
            )
        )
        existing = SessionModel(
            session_id="session-race",
            scenario_id="scenario-race",
            started_at=started_at,
            completed_at=None,
            status="active",
        )
        lookups = iter([None, existing])
        monkeypatch.setattr(
            repository,
            "get_by_session_id",
            lambda _session_id: next(lookups),
        )

        def fail_create(_session: SessionModel) -> SessionModel:
            raise IntegrityError("INSERT", {}, Exception("duplicate"))

        monkeypatch.setattr(repository, "create", fail_create)
        service = SessionService(repository, scenario_repository)

        with pytest.raises(DuplicateSessionError):
            service.create(
                SessionCreate(
                    scenario_id="scenario-race",
                    session_id="session-race",
                )
            )


def test_event_service_maps_unique_race_to_duplicate(
    test_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with Session(test_engine) as database_session:
        repository = EventRepository(database_session)
        existing = Event(
            event_id="event-race",
            timestamp=datetime.now(UTC),
            session_id="session-race",
            scenario_id="scenario-race",
            event_type="scenario_opened",
            source="browser",
            metadata_={},
        )
        lookups = iter([None, existing])
        monkeypatch.setattr(
            repository,
            "get_by_event_id",
            lambda _event_id: next(lookups),
        )

        def fail_create(_event: Event) -> Event:
            raise IntegrityError("INSERT", {}, Exception("duplicate"))

        monkeypatch.setattr(repository, "create", fail_create)
        service = TelemetryService(repository, EventConnectionManager())
        event_data = EventCreate(
            event_id="event-race",
            session_id="session-race",
            scenario_id="scenario-race",
            event_type="scenario_opened",
            source="browser",
        )

        with pytest.raises(DuplicateEventError):
            asyncio.run(service.record_event(event_data))


def test_service_does_not_hide_unrelated_integrity_error(
    test_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with Session(test_engine) as database_session:
        repository = ScenarioRepository(database_session)
        lookups = iter([None, None])
        monkeypatch.setattr(
            repository,
            "get_by_scenario_id",
            lambda _scenario_id: next(lookups),
        )

        def fail_create(_scenario: Scenario) -> Scenario:
            raise IntegrityError("INSERT", {}, Exception("unrelated"))

        monkeypatch.setattr(repository, "create", fail_create)
        service = ScenarioService(repository)

        with pytest.raises(IntegrityError):
            service.create(
                ScenarioCreate(
                    scenario_id="scenario-unrelated",
                    name="Scenario",
                    scenario_type="credential",
                )
            )
