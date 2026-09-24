import re

from app.enrichment.base import EnrichmentModule
from app.models.item import Item

# Matches a literal CPE 2.3 URI when an advisory prints one directly, e.g.
# cpe:2.3:a:ivanti:connect_secure:*:*:*:*:*:*:*:*
# Resolving a CPE from a bare vendor/product name (when the text has no
# literal CPE string) needs a dictionary lookup against the NVD CPE catalog
# and is deliberately left as future work.
_CPE_PATTERN = re.compile(r"cpe:2\.3(?::[^\s\"'<>]+)+", re.IGNORECASE)


class CpeExtractor(EnrichmentModule):
    name = "cpe_extractor"
    version = "1"
    source_toggle = "enrich_cpe"

    def run(self, item: Item) -> dict:
        text = " ".join(filter(None, [item.title, item.extracted_text]))
        cpe_ids = sorted({match.lower() for match in _CPE_PATTERN.findall(text)})
        return {"cpe_ids": cpe_ids}
