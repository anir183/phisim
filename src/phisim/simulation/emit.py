from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from phisim.infra.sqlite.repos.event import EventRepository
from phisim.telemetry.schemas import EventCreate
from phisim.telemetry.service import TelemetryService
from phisim.telemetry.websocket import manager


async def emit_event(
    session: Session,
    *,
    session_id: str,
    scenario_id: str,
    event_type: str,
    source: str,
    metadata: dict[str, Any],
) -> None:
    repository = EventRepository(session)
    service = TelemetryService(repository, manager)

    await service.record_event(
        EventCreate(
            event_id=uuid4().hex,
            session_id=session_id,
            scenario_id=scenario_id,
            event_type=event_type,
            source=source,
            metadata=metadata,
        )
    )
