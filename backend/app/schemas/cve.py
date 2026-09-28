import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict


class CveReference(BaseModel):
    url: str
    tags: list[str] = []


class CveLinkedItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    url: str
    published_at: dt.datetime | None


class CveOut(BaseModel):
    """Lightweight row for the CVE list — no description/cpes/references,
    which can be large and aren't needed until a single CVE is opened.
    """

    model_config = ConfigDict(from_attributes=True)

    cve_id: str
    title: str | None
    cvss_v3_score: float | None
    cvss_v4_score: float | None
    epss_score: float | None
    in_kev: bool
    fetched_at: dt.datetime | None


class CveDetailOut(CveOut):
    description: str | None
    cvss_v3_vector: str | None
    cvss_v4_vector: str | None
    kev_date_added: dt.datetime | None
    cpes: list[str] = []
    weaknesses: list[str] = []
    references: list[CveReference] = []
    items: list[CveLinkedItem] = []
