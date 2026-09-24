from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from phisim.infra.sqlite.models.scenario import Scenario


class ScenarioRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, scenario: Scenario) -> Scenario:
        self.session.add(scenario)

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

        self.session.refresh(scenario)

        return scenario

    def get_by_scenario_id(self, scenario_id: str) -> Scenario | None:
        statement = select(Scenario).where(Scenario.scenario_id == scenario_id)

        return self.session.scalar(statement)

    def list_all(self) -> list[Scenario]:
        statement = select(Scenario).order_by(
            Scenario.created_at,
            Scenario.scenario_id,
        )

        return list(self.session.scalars(statement))
