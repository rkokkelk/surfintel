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
    description: str | None
    published_at: dt.datetime | None
    status: ItemStatus
    last_changed_at: dt.datetime | None
    created_at: dt.datetime
    source: SourceOut
    # Populated by the route (batched, not a lazy relationship) — the feed
    # view needs severity/category/CVE badges without a request per item.
    enrichments: list[ItemEnrichmentOut] = []
    # Mirrors the cve_extractor enrichment's own fields (its data dict already
    # computes these as the worst-case across every CVE mentioned) — surfaced
    # at the top level so the feed/overview UI doesn't need to know module
    # names just to render a CVSS/KEV/EPSS badge.
    max_cvss_score: float | None = None
    max_epss_score: float | None = None
    in_kev: bool = False


class ItemDetailOut(ItemOut):
    extracted_text: str | None
