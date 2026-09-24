import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.source import SourceType


class SourceCreate(BaseModel):
    name: str
    type: SourceType
    config: dict
    poll_interval_seconds: int = 3600
    enrich_cve: bool = True
    enrich_cpe: bool = True
    enrich_kev: bool = True
    enrich_ai: bool = True

class SourceIngestion(BaseModel):
    """All fields optional — only what's set gets changed (PATCH semantics)."""

    fetch_backend: str | None = None
    force: bool = False

class SourceUpdate(BaseModel):
    """All fields optional — only what's set gets changed (PATCH semantics)."""

    name: str | None = None
    type: SourceType | None = None
    config: dict | None = None
    enabled: bool | None = None
    poll_interval_seconds: int | None = None
    enrich_cve: bool | None = None
    enrich_cpe: bool | None = None
    enrich_kev: bool | None = None
    enrich_ai: bool | None = None


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: SourceType
    config: dict
    enabled: bool
    enrich_cve: bool
    enrich_cpe: bool
    enrich_kev: bool
    enrich_ai: bool
    favicon: str | None = None
    poll_interval_seconds: int
    last_polled_at: dt.datetime | None
