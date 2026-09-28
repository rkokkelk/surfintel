import os
import re

import httpx

from app.enrichment.base import EnrichmentModule
from app.models.item import Item

_CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)


class CveExtractor(EnrichmentModule):
    name = "cve_extractor"
    version = "1"
    source_toggle = "enrich_cve"

    def __init__(self):
        self.url = "https://app.opencve.io/api/v2"
        self.headers = {
            'Authorization': f'Bearer {os.environ.get('OPENCVE_API_KEY')}'
        }

    def _fetch_opencve_info(self, cve_id: str) -> dict:
        url = f"{self.url}/cves/{cve_id}"
        response = httpx.get(url, headers=self.headers, params={'include': 'nvd_cpe_configurations,references'})

        if 400 <= response.status_code < 500:
            return {}
        elif 200 <= response.status_code < 300:
            return response.json()
        else:
            response.raise_for_status()

        return {}

    def run(self, item: Item) -> dict:
        result = {}

        text = " ".join(filter(None, [item.title, item.extracted_text]))
        cve_ids = sorted({match.upper() for match in _CVE_PATTERN.findall(text)})

        for cve_id in cve_ids:
            result[cve_id] = self._fetch_opencve_info(cve_id)

        return result

    def match_fields(self, data: dict) -> dict:
        return {"cve_id": data.keys()}
