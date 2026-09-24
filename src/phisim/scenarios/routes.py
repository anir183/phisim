from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from phisim.infra.sqlite.connection import get_session
from phisim.infra.sqlite.repos.scenario import ScenarioRepository
from phisim.scenarios.schemas import ScenarioCreate, ScenarioResponse
from phisim.scenarios.service import (
    DuplicateScenarioError,
    ScenarioNotFoundError,
    ScenarioService,
)

router = APIRouter(
    prefix="/api/scenarios",
    tags=["scenarios"],
)


@router.post("", response_model=ScenarioResponse, status_code=201)
def create_scenario(
    scenario_data: ScenarioCreate,
    session: Annotated[Session, Depends(get_session)],
) -> ScenarioResponse:
    service = ScenarioService(ScenarioRepository(session))

    try:
        scenario = service.create(scenario_data)
    except DuplicateScenarioError:
        raise HTTPException(
            status_code=409,
            detail="Scenario with this scenario_id already exists.",
        ) from None

    return ScenarioResponse.model_validate(scenario)


@router.get("", response_model=list[ScenarioResponse])
def list_scenarios(
    session: Annotated[Session, Depends(get_session)],
) -> list[ScenarioResponse]:
    service = ScenarioService(ScenarioRepository(session))

    return [
        ScenarioResponse.model_validate(scenario)
        for scenario in service.list_all()
    ]


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(
    scenario_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> ScenarioResponse:
    service = ScenarioService(ScenarioRepository(session))

    try:
        scenario = service.get(scenario_id)
    except ScenarioNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Scenario not found.",
        ) from None

    return ScenarioResponse.model_validate(scenario)
