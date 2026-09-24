# ruff: noqa: B008

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session

from phisim.infra.sqlite.connection import get_session
from phisim.infra.sqlite.models.event import Event
from phisim.infra.sqlite.repos.event import EventRepository
from phisim.telemetry.schemas import EventCreate, EventResponse
from phisim.telemetry.service import (
    DuplicateEventError,
    TelemetryService,
    UnsafeEventMetadataError,
)
from phisim.telemetry.websocket import manager

router = APIRouter(
    prefix="/api/events",
    tags=["telemetry"],
)


def _event_response(event: Event) -> EventResponse:
    return EventResponse(
        id=event.id,
        event_id=event.event_id,
        timestamp=event.timestamp,
        session_id=event.session_id,
        scenario_id=event.scenario_id,
        event_type=event.event_type,
        source=event.source,
        metadata=event.metadata_,
    )


@router.post("", response_model=EventResponse, status_code=201)
async def create_event(
    event_data: EventCreate,
    session: Session = Depends(get_session),
) -> EventResponse:
    repository = EventRepository(session)
    service = TelemetryService(repository, manager)

    try:
        event = await service.record_event(event_data)
    except DuplicateEventError:
        raise HTTPException(
            status_code=409,
            detail="Event with this event_id already exists.",
        ) from None
    except UnsafeEventMetadataError:
        raise HTTPException(
            status_code=422,
            detail="Event metadata contains forbidden credential data.",
        ) from None

    return _event_response(event)


@router.get("", response_model=list[EventResponse])
def list_events(
    session_id: str = Query(min_length=1, max_length=64),
    session: Session = Depends(get_session),
) -> list[EventResponse]:
    repository = EventRepository(session)

    return [
        _event_response(event)
        for event in repository.list_by_session(session_id)
    ]


@router.websocket("/ws")
async def event_stream(websocket: WebSocket) -> None:
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
