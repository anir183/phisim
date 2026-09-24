from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.models.simulation_environment import (
    SimulationEnvironment,
)


class SimulationEnvironmentRepository:
    def __init__(self, session: OrmSession) -> None:
        self.session = session

    def create(
        self, environment: SimulationEnvironment
    ) -> SimulationEnvironment:
        self.session.add(environment)
        self.session.commit()
        self.session.refresh(environment)
        return environment

    def get_by_token(self, token: str) -> SimulationEnvironment | None:
        return self.session.scalar(
            select(SimulationEnvironment).where(
                SimulationEnvironment.token == token
            )
        )

    def get_by_session_id(
        self,
        session_id: str,
    ) -> SimulationEnvironment | None:
        return self.session.scalar(
            select(SimulationEnvironment).where(
                SimulationEnvironment.session_id == session_id
            )
        )

    def save(
        self,
        environment: SimulationEnvironment,
    ) -> SimulationEnvironment:
        environment.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(environment)
        return environment
