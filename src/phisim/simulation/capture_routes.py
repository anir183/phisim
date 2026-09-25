from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.connection import get_session
from phisim.infra.sqlite.repos.simulation_attack import (
    SimulationAttackRepository,
)
from phisim.simulation.capture import (
    list_sandbox_captures,
    sandbox_capture_enabled,
)

router = APIRouter(
    prefix="/api/sandbox",
    tags=["sandbox-capture"],
)


@router.get("/captures")
def sandbox_captures(
    response: Response,
    session_id: Annotated[str, Query(min_length=1, max_length=64)],
    database_session: Annotated[OrmSession, Depends(get_session)],
) -> dict[str, object]:
    response.headers["Cache-Control"] = "no-store"
    enabled = sandbox_capture_enabled()
    captures = (
        list_sandbox_captures(database_session, session_id) if enabled else []
    )
    if enabled and not captures:
        attack = SimulationAttackRepository(
            database_session
        ).get_by_victim_session_id(session_id)
        if attack is not None:
            captures = list_sandbox_captures(
                database_session,
                attack.operator_session_id,
            )
    return {
        "enabled": enabled,
        "captures": captures,
    }
