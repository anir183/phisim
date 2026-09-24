from datetime import UTC, datetime

from phisim.infra.sqlite.models.event import Event
from phisim.infra.sqlite.repos.event import EventRepository
from phisim.telemetry.schemas import EventCreate
from phisim.telemetry.websocket import EventConnectionManager


class DuplicateEventError(Exception):
    pass


class TelemetryService:
    def __init__(
        self,
        repository: EventRepository,
        broadcaster: EventConnectionManager,
    ) -> None:
        self.repository = repository
        self.broadcaster = broadcaster

    async def record_event(self, event_data: EventCreate) -> Event:
        if self.repository.get_by_event_id(event_data.event_id) is not None:
            raise DuplicateEventError(event_data.event_id)

        event = Event(
            event_id=event_data.event_id,
            timestamp=datetime.now(UTC),
            session_id=event_data.session_id,
            scenario_id=event_data.scenario_id,
            event_type=event_data.event_type,
            source=event_data.source,
            metadata_=event_data.metadata,
        )

        event = self.repository.create(event)

        await self.broadcaster.broadcast(
            {
                "id": event.id,
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "session_id": event.session_id,
                "scenario_id": event.scenario_id,
                "event_type": event.event_type,
                "source": event.source,
                "metadata": event.metadata_,
            }
        )

        return event
