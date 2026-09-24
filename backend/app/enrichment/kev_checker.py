import datetime as dt

import httpx

from app.enrichment.base import EnrichmentModule
from app.models.item import Item

_KEV_FEED_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
_CACHE_TTL = dt.timedelta(hours=6)


class KevChecker(EnrichmentModule):
    """Depends on CveExtractor having already run in this pass — reads its
    cve_ids from prior_results rather than re-extracting them.
    """

    name = "kev_checker"
    version = "1"
    source_toggle = "enrich_kev"

    def __init__(self) -> None:
        self._cached_ids: set[str] | None = None
        self._cached_at: dt.datetime | None = None

    def run(self, item: Item, prior_results: dict[str, dict]) -> dict:
        cve_ids: list[str] = prior_results.get("cve_extractor", {}).get("cve_ids", [])
        if not cve_ids:
            return {"in_kev": False, "matched_cve_ids": []}

        kev_ids = self._kev_cve_ids()
        matched = sorted(set(cve_ids) & kev_ids)
        return {"in_kev": bool(matched), "matched_cve_ids": matched}

    def match_fields(self, data: dict) -> dict:
        return {"severity": ["kritiek"]} if data.get("in_kev") else {}

    def _kev_cve_ids(self) -> set[str]:
        now = dt.datetime.now(dt.timezone.utc)
        if self._cached_ids is not None and self._cached_at is not None:
            if now - self._cached_at < _CACHE_TTL:
                return self._cached_ids

        try:
            response = httpx.get(_KEV_FEED_URL, timeout=10.0)
            response.raise_for_status()
            vulnerabilities = response.json().get("vulnerabilities", [])
            self._cached_ids = {v["cveID"].upper() for v in vulnerabilities if v.get("cveID")}
            self._cached_at = now
        except httpx.HTTPError:
            # KEV lookup is best-effort enrichment, never a reason to fail the
            # whole pipeline — fall back to the last good cache, or empty.
            self._cached_ids = self._cached_ids or set()

        return self._cached_ids
