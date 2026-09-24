from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.models.simulation_run import SimulationRun


class SimulationRunRepository:
    def __init__(self, session: OrmSession) -> None:
        self.session = session

    def create(self, run: SimulationRun) -> SimulationRun:
        self.session.add(run)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        self.session.refresh(run)
        return run

    def get_by_run_id(self, run_id: str) -> SimulationRun | None:
        return self.session.scalar(
            select(SimulationRun).where(SimulationRun.run_id == run_id)
        )

    def get_by_session_and_scenario(
        self,
        session_id: str,
        scenario_id: str,
    ) -> SimulationRun | None:
        return self.session.scalar(
            select(SimulationRun).where(
                SimulationRun.session_id == session_id,
                SimulationRun.scenario_id == scenario_id,
            )
        )

    def list_by_session(self, session_id: str) -> list[SimulationRun]:
        return list(
            self.session.scalars(
                select(SimulationRun)
                .where(SimulationRun.session_id == session_id)
                .order_by(SimulationRun.started_at, SimulationRun.run_id)
            )
        )

    def save(self, run: SimulationRun) -> SimulationRun:
        run.updated_at = datetime.now(UTC)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        self.session.refresh(run)
        return run
