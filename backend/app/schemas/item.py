import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.item import ItemStatus
from app.schemas.source import SourceOut


class ItemEnrichmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    module_name: str
    module_version: str
    data: dict


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    url: str
    title: str | None
    published_at: dt.datetime | None
    status: ItemStatus
    last_changed_at: dt.datetime | None
    created_at: dt.datetime
    source: SourceOut
    # Populated by the route (batched, not a lazy relationship) — the feed
    # view needs severity/category/CVE badges without a request per item.
    enrichments: list[ItemEnrichmentOut] = []


class ItemDetailOut(ItemOut):
    extracted_text: str | None
