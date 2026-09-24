"""Severity/category classification.

This first version is a plain keyword heuristic, not an LLM call — no AI
provider/API key has been chosen for the project yet. It is a genuine,
working v1 (not a stub): swapping it for an LLM-backed classifier later is a
drop-in replacement behind the same EnrichmentModule interface, and the
result shape (`severity`, `category`) stays the same either way.
"""

from app.enrichment.base import EnrichmentModule
from app.models.item import Item

_SEVERITY_KEYWORDS = {
    "kritiek": ["critical", "kritiek", "actively exploited", "actief misbruikt", "zero-day", "zero day"],
    "hoog": ["high severity", "hoog risico", "remote code execution", "authentication bypass", "authenticatie-bypass"],
    "midden": ["medium severity", "gemiddeld risico"],
}

_CATEGORY_KEYWORDS = {
    "patch": ["patch", "update", "fix", "hotfix"],
    "malware": ["malware", "ransomware", "phishing", "campaign", "campagne", "actor"],
    "advisory": ["advisory", "bulletin", "kev", "vulnerability", "kwetsbaarheid"],
}


class AiCategorizer(EnrichmentModule):
    name = "ai_categorizer"
    version = "1-heuristic"
    source_toggle = "enrich_ai"

    def run(self, item: Item) -> dict:
        text = " ".join(filter(None, [item.title, item.extracted_text])).lower()

        severity = next((level for level, kws in _SEVERITY_KEYWORDS.items() if any(kw in text for kw in kws)), None)
        category = next((cat for cat, kws in _CATEGORY_KEYWORDS.items() if any(kw in text for kw in kws)), None)

        return {"severity": severity, "category": category}

    def match_fields(self, data: dict) -> dict:
        fields: dict[str, list[str]] = {}
        if data.get("severity"):
            fields["severity"] = [data["severity"]]
        if data.get("category"):
            fields["category"] = [data["category"]]
        return fields
