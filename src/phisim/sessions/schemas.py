from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class SessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"


class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1, max_length=64)
    session_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
    )


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    scenario_id: str
    started_at: datetime
    completed_at: datetime | None
    status: SessionStatus
