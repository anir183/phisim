from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CredentialSubmissionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_presence: dict[str, bool] = Field(default_factory=dict)


class EventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=64)
    session_id: str = Field(min_length=1, max_length=64)
    scenario_id: str = Field(min_length=1, max_length=64)
    event_type: str = Field(min_length=1, max_length=64)
    source: str = Field(min_length=1, max_length=32)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventResponse(EventCreate):
    id: int
    timestamp: datetime
