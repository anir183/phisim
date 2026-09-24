from datetime import UTC, datetime

from phisim.infra.sqlite.models.scenario import Scenario
from phisim.infra.sqlite.repos.scenario import ScenarioRepository
from phisim.scenarios.schemas import ScenarioCreate


class DuplicateScenarioError(Exception):
    pass


class ScenarioNotFoundError(Exception):
    pass


class ScenarioService:
    def __init__(self, repository: ScenarioRepository) -> None:
        self.repository = repository

    def create(self, scenario_data: ScenarioCreate) -> Scenario:
        if (
            self.repository.get_by_scenario_id(scenario_data.scenario_id)
            is not None
        ):
            raise DuplicateScenarioError

        scenario = Scenario(
            scenario_id=scenario_data.scenario_id,
            name=scenario_data.name,
            scenario_type=scenario_data.scenario_type,
            description=scenario_data.description,
            created_at=datetime.now(UTC),
        )

        return self.repository.create(scenario)

    def get(self, scenario_id: str) -> Scenario:
        scenario = self.repository.get_by_scenario_id(scenario_id)

        if scenario is None:
            raise ScenarioNotFoundError

        return scenario

    def list_all(self) -> list[Scenario]:
        return self.repository.list_all()
