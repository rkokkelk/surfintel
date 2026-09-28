import datetime as dt
import os
import re

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enrichment.base import EnrichmentModule
from app.models.cve import Cve, ItemCve
from app.models.item import Item

_CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)

# How long a cached Cve row is trusted before we ask OpenCVE again — CVE
# metadata (CVSS, KEV, EPSS) does change after publication, but not often
# enough to justify hitting a rate-limited API on every mention.
_REFRESH_INTERVAL = dt.timedelta(hours=24)


class CveExtractor(EnrichmentModule):
    name = "cve_extractor"
    version = "2"
    source_toggle = "enrich_cve"

    def __init__(self):
        self.url = "https://app.opencve.io/api/v2"
        self.headers = {"Authorization": f"Bearer {os.environ.get('OPENCVE_API_KEY')}"}

    def run(self, item: Item, db: Session) -> dict:
        text = " ".join(filter(None, [item.title, item.extracted_text]))
        cve_ids = sorted({match.upper() for match in _CVE_PATTERN.findall(text)})

        cves = [self._sync_cve(db, cve_id) for cve_id in cve_ids]

        for cve_id in cve_ids:
            exists = db.scalar(select(ItemCve).where(ItemCve.item_id == item.id, ItemCve.cve_id == cve_id))
            if not exists:
                db.add(ItemCve(item_id=item.id, cve_id=cve_id))

        # Alert conditions on cvss_score/epss_score/kev (see match_fields
        # below) match against the item as a whole, so a mention of several
        # CVEs is judged by its worst one — the max, not e.g. the average.
        cvss_scores = [c.cvss_v4_score if c.cvss_v4_score is not None else c.cvss_v3_score for c in cves]
        cvss_scores = [s for s in cvss_scores if s is not None]
        epss_scores = [c.epss_score for c in cves if c.epss_score is not None]

        return {
            "cve_ids": cve_ids,
            "max_cvss_score": max(cvss_scores) if cvss_scores else None,
            "max_epss_score": max(epss_scores) if epss_scores else None,
            "in_kev": any(c.in_kev for c in cves),
        }

    def match_fields(self, data: dict) -> dict:
        fields: dict[str, list[str]] = {"cve_id": data.get("cve_ids", [])}
        if data.get("max_cvss_score") is not None:
            fields["cvss_score"] = [str(data["max_cvss_score"])]
        if data.get("max_epss_score") is not None:
            fields["epss_score"] = [str(data["max_epss_score"])]
        if data.get("in_kev"):
            fields["kev"] = ["true"]
        return fields

    def _sync_cve(self, db: Session, cve_id: str) -> Cve:
        now = dt.datetime.now(dt.timezone.utc)
        existing = db.get(Cve, cve_id)
        if existing and existing.fetched_at and now - existing.fetched_at < _REFRESH_INTERVAL:
            return existing

        payload = self._fetch_opencve_info(cve_id)
        cve = existing or Cve(cve_id=cve_id)

        if payload:
            _apply_opencve_payload(cve, payload)
        cve.fetched_at = now

        if not existing:
            db.add(cve)
        return cve

    def _fetch_opencve_info(self, cve_id: str) -> dict:
        url = f"{self.url}/cves/{cve_id}"
        response = httpx.get(
            url, headers=self.headers, params={"include": "nvd_cpe_configurations,references"}, timeout=20
        )

        if 400 <= response.status_code < 500:
            return {}
        if 200 <= response.status_code < 300:
            return response.json()
        response.raise_for_status()
        return {}


def _apply_opencve_payload(cve: Cve, payload: dict) -> None:
    metrics = payload.get("metrics", {})

    def score_vector(*keys: str) -> tuple[float | None, str | None]:
        """First key with actual data wins — cvssV3_1 over cvssV3_0, say."""
        for key in keys:
            data = (metrics.get(key) or {}).get("data") or {}
            if data:
                return data.get("score"), data.get("vector")
        return None, None

    cve.title = payload.get("title")
    cve.description = payload.get("description")

    cve.cvss_v3_score, cve.cvss_v3_vector = score_vector("cvssV3_1", "cvssV3_0")
    cve.cvss_v4_score, cve.cvss_v4_vector = score_vector("cvssV4_0")
    cve.epss_score = ((metrics.get("epss") or {}).get("data") or {}).get("score")

    kev_data = (metrics.get("kev") or {}).get("data")
    cve.in_kev = bool(kev_data)
    cve.kev_date_added = kev_data.get("dateAdded") if kev_data else None

    cve.cpes = sorted(
        {
            match["criteria"]
            for group in payload.get("nvd_cpe_configurations", [])
            for node in group.get("nodes", [])
            for match in node.get("cpeMatch", [])
            if match.get("criteria")
        }
    )
    cve.weaknesses = payload.get("weaknesses", [])

    # OpenCVE repeats the same reference URL once per CNA source that filed
    # it — dedupe by URL, merging tags, rather than showing the same link
    # three times.
    by_url: dict[str, set[str]] = {}
    for ref in payload.get("references", []):
        url = ref.get("url")
        if not url:
            continue
        by_url.setdefault(url, set()).update(ref.get("tags", []))
    cve.references = [{"url": url, "tags": sorted(tags)} for url, tags in by_url.items()]

    cve.raw_data = payload
