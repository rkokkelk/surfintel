import re

from app.enrichment.base import EnrichmentModule
from app.models.item import Item

_CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)


class CveExtractor(EnrichmentModule):
    name = "cve_extractor"
    version = "1"

    def run(self, item: Item, prior_results: dict[str, dict]) -> dict:
        text = " ".join(filter(None, [item.title, item.extracted_text]))
        cve_ids = sorted({match.upper() for match in _CVE_PATTERN.findall(text)})
        return {"cve_ids": cve_ids}

    def match_fields(self, data: dict) -> dict:
        return {"cve_id": data.get("cve_ids", [])}
