from datetime import UTC, datetime

from pydantic import ValidationError

from phisim.infra.sqlite.models.event import Event
from phisim.infra.sqlite.repos.event import EventRepository
from phisim.telemetry.schemas import CredentialSubmissionMetadata, EventCreate
from phisim.telemetry.websocket import EventConnectionManager


class DuplicateEventError(Exception):
    pass


class UnsafeEventMetadataError(Exception):
    pass


_FORBIDDEN_CREDENTIAL_KEYS = frozenset(
    {
        "credential",
        "credentials",
        "passwd",
        "password",
        "password_hash",
        "passwordhash",
        "pwd",
        "raw_credential",
        "raw_credentials",
        "rawcredential",
        "rawcredentials",
        "user_name",
        "username",
    }
)


def _is_safe_field_presence(value: object) -> bool:
    return isinstance(value, dict) and all(
        isinstance(field_value, bool) for field_value in value.values()
    )


def _contains_forbidden_credential(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            normalized_key = (
                str(key).casefold().replace("-", "_").replace(" ", "_")
            )

            if normalized_key == "field_presence":
                if not _is_safe_field_presence(nested_value):
                    return True
                continue

            if normalized_key in _FORBIDDEN_CREDENTIAL_KEYS:
                return True

            if _contains_forbidden_credential(nested_value):
                return True

        return False

    if isinstance(value, list):
        return any(_contains_forbidden_credential(item) for item in value)

    return False


class TelemetryService:
    def __init__(
        self,
        repository: EventRepository,
        broadcaster: EventConnectionManager,
    ) -> None:
        self.repository = repository
        self.broadcaster = broadcaster

    async def record_event(self, event_data: EventCreate) -> Event:
        if _contains_forbidden_credential(event_data.metadata):
            raise UnsafeEventMetadataError

        if event_data.event_type == "credential_submission_attempted":
            try:
                CredentialSubmissionMetadata.model_validate(event_data.metadata)
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
