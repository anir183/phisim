from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as OrmSession

from phisim.analysis.schemas import Indicator
from phisim.analysis.session import aggregate_session_indicators
from phisim.infra.sqlite.connection import get_session
from phisim.infra.sqlite.models.event import Event
from phisim.infra.sqlite.repos.event import EventRepository
from phisim.infra.sqlite.repos.session import SessionRepository
from phisim.inspection.timeline import TimelineEntry, build_session_timeline
from phisim.telemetry.schemas import EventResponse

router = APIRouter(tags=["analysis"])


class SessionAnalysisResponse(BaseModel):
    session_id: str = Field(description="Analyzed Session identifier")
    indicators: list[Indicator] = Field(
        default_factory=list,
        description="Deduplicated indicators observed in the Session",
    )
    timeline: list[TimelineEntry] = Field(
        default_factory=list,
        description="Chronological Event explanations with indicators",
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


def _analyze_session(
    session_id: str,
    database_session: OrmSession,
) -> SessionAnalysisResponse:
    session_repository = SessionRepository(database_session)
    if session_repository.get_by_session_id(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    events = [
        _event_response(event)
        for event in EventRepository(database_session).list_by_session(
            session_id
        )
    ]
    return SessionAnalysisResponse(
        session_id=session_id,
        indicators=aggregate_session_indicators(events),
        timeline=build_session_timeline(events),
    )


@router.get(
    "/api/analysis/sessions/{session_id}",
    response_model=SessionAnalysisResponse,
)
def analyze_session(
    session_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> SessionAnalysisResponse:
    return _analyze_session(session_id, database_session)


@router.get(
    "/api/sessions/{session_id}/analysis",
    response_model=SessionAnalysisResponse,
)
def analyze_session_alias(
    session_id: str,
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> SessionAnalysisResponse:
    return _analyze_session(session_id, database_session)
