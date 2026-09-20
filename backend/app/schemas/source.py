import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.source import SourceType


class SourceCreate(BaseModel):
    name: str
    type: SourceType
    config: dict
    poll_interval_seconds: int = 3600


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: SourceType
    config: dict
    enabled: bool
    poll_interval_seconds: int
    last_polled_at: dt.datetime | None
