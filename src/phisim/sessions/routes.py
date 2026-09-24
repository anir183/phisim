from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.connection import get_session
from phisim.infra.sqlite.repos.scenario import ScenarioRepository
from phisim.infra.sqlite.repos.session import SessionRepository
from phisim.sessions.schemas import SessionCreate, SessionResponse
from phisim.sessions.service import (
    DuplicateSessionError,
    SessionNotFoundError,
    SessionScenarioNotFoundError,
    SessionService,
)

router = APIRouter(
    prefix="/api/sessions",
    tags=["sessions"],
)


@router.post("", response_model=SessionResponse, status_code=201)
def create_session(
    session_data: SessionCreate,
    session: Annotated[OrmSession, Depends(get_session)],
) -> SessionResponse:
    service = SessionService(
        SessionRepository(session),
        ScenarioRepository(session),
    )

    try:
        created_session = service.create(session_data)
    except SessionScenarioNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Scenario not found.",
        ) from None
    except DuplicateSessionError:
        raise HTTPException(
            status_code=409,
            detail="Session with this session_id already exists.",
        ) from None

    return SessionResponse.model_validate(created_session)


@router.get("", response_model=list[SessionResponse])
def list_sessions(
    session: Annotated[OrmSession, Depends(get_session)],
) -> list[SessionResponse]:
    service = SessionService(
        SessionRepository(session),
        ScenarioRepository(session),
    )

    return [
        SessionResponse.model_validate(existing_session)
        for existing_session in service.list_all()
    ]


@router.get("/{session_id}", response_model=SessionResponse)
def get_session_details(
    session_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> SessionResponse:
    service = SessionService(
        SessionRepository(session),
        ScenarioRepository(session),
    )

    try:
        existing_session = service.get(session_id)
    except SessionNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Session not found.",
        ) from None

    return SessionResponse.model_validate(existing_session)


@router.post("/{session_id}/complete", response_model=SessionResponse)
def complete_session(
    session_id: str,
    session: Annotated[OrmSession, Depends(get_session)],
) -> SessionResponse:
    service = SessionService(
        SessionRepository(session),
        ScenarioRepository(session),
    )

    try:
        completed_session = service.complete(session_id)
    except SessionNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Session not found.",
        ) from None

    return SessionResponse.model_validate(completed_session)
