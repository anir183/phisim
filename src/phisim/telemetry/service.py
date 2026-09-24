from datetime import UTC, datetime

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from phisim.analysis.engine import analyze_event
from phisim.infra.sqlite.models.event import Event
from phisim.infra.sqlite.repos.event import EventRepository
from phisim.security.guardrails import (
    UnsafeMetadataError,
    enforce_safe_event_metadata,
)
from phisim.telemetry.schemas import (
    CredentialSubmissionMetadata,
    EventCreate,
    EventResponse,
)
from phisim.telemetry.websocket import EventConnectionManager
from phisim.utils.datetime import serialize_utc_datetime


class DuplicateEventError(Exception):
    pass


class UnsafeEventMetadataError(Exception):
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
        try:
            safe_metadata = enforce_safe_event_metadata(event_data.metadata)
        except UnsafeMetadataError:
            raise UnsafeEventMetadataError from None

        if event_data.event_type == "credential_submission_attempted":
            try:
                CredentialSubmissionMetadata.model_validate(safe_metadata)
            except ValidationError:
                raise UnsafeEventMetadataError from None

        if self.repository.get_by_event_id(event_data.event_id) is not None:
            raise DuplicateEventError(event_data.event_id)

        event = Event(
            event_id=event_data.event_id,
            timestamp=datetime.now(UTC),
            session_id=event_data.session_id,
            scenario_id=event_data.scenario_id,
            event_type=event_data.event_type,
            source=event_data.source,
            metadata_=safe_metadata,
        )

        try:
            event = self.repository.create(event)
        except IntegrityError:
            if self.repository.get_by_event_id(event_data.event_id) is not None:
                raise DuplicateEventError(event_data.event_id) from None

            raise

        event_response = EventResponse(
            id=event.id,
            event_id=event.event_id,
            timestamp=event.timestamp,
            session_id=event.session_id,
            scenario_id=event.scenario_id,
            event_type=event.event_type,
            source=event.source,
            metadata=event.metadata_,
        )
        indicators = analyze_event(event_response)
        indicator_dicts = [i.model_dump() for i in indicators]

        await self.broadcaster.broadcast(
            {
                "id": event.id,
                "event_id": event.event_id,
                "timestamp": serialize_utc_datetime(event.timestamp),
                "session_id": event.session_id,
                "scenario_id": event.scenario_id,
                "event_type": event.event_type,
                "source": event.source,
                "metadata": event.metadata_,
                "indicators": indicator_dicts,
            }
        )

        return event
