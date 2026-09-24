from pydantic import BaseModel, ConfigDict, Field

from phisim.utils.datetime import UtcDateTime


class ScenarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    scenario_type: str = Field(min_length=1, max_length=64)
    description: str = Field(default="", max_length=2000)


class ScenarioResponse(ScenarioCreate):
    model_config = ConfigDict(from_attributes=True)

    created_at: UtcDateTime
