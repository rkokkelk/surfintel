import datetime as dt
import re

import httpx
from httpx_retries import Retry, RetryTransport
from loguru import logger
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

    def run(self, item: Item, db: Session) -> dict:
        self.log = logger.bind(source=item.source_id, item=item.id)
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

        max_cvss = max(cvss_scores) if cvss_scores else None
        max_epss = max(epss_scores) if cvss_scores else None

        self.log.info("finished {}! (cve={} cvss={} epss={} kev={})", self.name, len(cve_ids), max_cvss, max_epss, any(c.in_kev for c in cves))

        return {
            "cve_ids": cve_ids,
            "max_cvss_score": max_cvss,
            "max_epss_score": max_epss,
            "in_kev": any(c.in_kev for c in cves)
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
        now = dt.datetime.now(dt.UTC)
        existing = db.get(Cve, cve_id)

        if existing and existing.fetched_at and now - existing.fetched_at < _REFRESH_INTERVAL:
            self.log.trace("cached CVE: {} latest {}", cve_id, existing.fetched_at)
            return existing

        csaf = self._fetch_cve_info(cve_id)
        cve = existing or Cve(cve_id=cve_id)

        if csaf:
            _apply_csaf(cve, csaf)
        cve.fetched_at = now

        if not existing:
            db.add(cve)
        return cve

    def _fetch_cve_info(self, cve_id: str) -> dict:
        data = {}
        year = cve_id.split('-')[1]
        url = f"https://vulnerabilities.ncsc.nl/csaf/v2/{year}/{cve_id.lower()}.json"

        retry = Retry(total=5, backoff_factor=5)
        transport = RetryTransport(retry=retry)

        with httpx.Client(transport=transport) as client:
            response = client.get(
                url,timeout=20
            )

            try:
                response.raise_for_status()
                data = response.json()
                self.log.trace("Received CVE info for: {} - {}b", cve_id, response.num_bytes_downloaded)
            except httpx.HTTPStatusError as hse:
                self.log.warning("Failed to fetch CVE info for: {} - {}", cve_id, hse.response.text)

        return data

def _apply_csaf(cve: Cve, payload: dict) -> None:
    """Apply CSAF data to a Cve object.
    
    Supports both OpenCVE-style flat payloads and CSAF 2.0 format from NCSC.
    """
    # Check if this is a CSAF 2.0 document (has "document" and "vulnerabilities" keys)
    is_csaf_v2 = "document" in payload and "vulnerabilities" in payload
    
    if is_csaf_v2:
        _apply_csaf_v2(cve, payload)
    else:
        _apply_csaf_legacy(cve, payload)


def _apply_csaf_v2(cve: Cve, payload: dict) -> None:
    """Apply CSAF 2.0 format data (NCSC style) to a Cve object."""
    doc = payload.get("document", {})
    vulnerabilities = payload.get("vulnerabilities", [])
    vuln = vulnerabilities[0]
    
    # Title: prefer vulnerability title, then document title
    cve.title = vuln.get("title") or doc.get("title")
    
    # Description: extract from notes with category "description"
    description_notes = [
        note.get("text") 
        for note in vuln.get("notes", []) 
        if note.get("category") == "description"
    ]
    cve.description = description_notes[0] if description_notes else None
    
    # CVSS scores: extract from scores array
    def extract_cvss_scores(scores_list: list) -> tuple[float | None, str | None, float | None, str | None]:
        """Extract CVSS v3 and v4 scores from CSAF scores array."""
        cvss_v3_score = None
        cvss_v3_vector = None
        cvss_v4_score = None
        cvss_v4_vector = None
        
        for score in scores_list or []:
            if "cvss_v3" in score:
                cvss_data = score.get("cvss_v3", {})
                cvss_v3_score = cvss_data.get("baseScore")
                cvss_v3_vector = cvss_data.get("vectorString")
            if "cvss_v4" in score:
                cvss_data = score.get("cvss_v4", {})
                cvss_v4_score = cvss_data.get("baseScore")
                cvss_v4_vector = cvss_data.get("vectorString")
        
        return cvss_v3_score, cvss_v3_vector, cvss_v4_score, cvss_v4_vector
    
    scores = vuln.get("scores", [])
    cve.cvss_v3_score, cve.cvss_v3_vector, cve.cvss_v4_score, cve.cvss_v4_vector = extract_cvss_scores(scores)
    
    # EPSS score: extract from notes with category "other" and title "EPSS"
    epss_notes = [
        note.get("text") 
        for note in vuln.get("notes", []) 
        if note.get("category") == "other" and note.get("title") == "EPSS"
    ]
    epss_text = epss_notes[0] if epss_notes else None
    try:
        cve.epss_score = float(epss_text) if epss_text else None
    except (ValueError, TypeError):
        cve.epss_score = None
    
    # KEV: Not available in NCSC CSAF, so set to False/None
    cve.in_kev = False
    cve.kev_date_added = None
    
    # CPES: extract from product_tree and product_identification_helper
    def extract_cpes_from_tree(tree: dict | list) -> list[str]:
        """Recursively extract CPEs from product tree."""
        cpes = []
        
        if isinstance(tree, list):
            for item in tree:
                cpes.extend(extract_cpes_from_tree(item))
        elif isinstance(tree, dict):
            # Check for product_identification_helper
            helper = tree.get("product_identification_helper", {})
            if helper and "cpe" in helper:
                cpes.append(helper["cpe"])
            
            # Recursively check branches
            for branch in tree.get("branches", []):
                cpes.extend(extract_cpes_from_tree(branch))
            
            # Check product directly
            product = tree.get("product", {})
            helper = product.get("product_identification_helper", {})
            if helper and "cpe" in helper:
                cpes.append(helper["cpe"])
        
        return cpes
    
    product_tree = payload.get("product_tree", {})
    cpes = extract_cpes_from_tree(product_tree)
    cve.cpes = sorted(set(cpes)) if cpes else []
    
    # Weaknesses: extract CWE information
    cwe = vuln.get("cwe", {})
    if cwe:
        cve.weaknesses = [{"id": cwe.get("id"), "name": cwe.get("name"), "type": "CWE"}]
    else:
        cve.weaknesses = []
    
    # References: extract from vulnerability references
    vuln_refs = vuln.get("references", [])
    by_url: dict[str, set[str]] = {}
    for ref in vuln_refs:
        url = ref.get("url")
        if not url:
            continue
        # Use summary as tag if available
        tags = [ref.get("summary", "")] if ref.get("summary") else []
        by_url.setdefault(url, set()).update(tags)
    cve.references = [{"url": url, "tags": sorted(tags)} for url, tags in by_url.items()]
    
    # Raw data: store the entire payload
    cve.raw_data = payload


def _apply_csaf_legacy(cve: Cve, payload: dict) -> None:
    """Apply legacy OpenCVE-style CSAF data to a Cve object."""
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
