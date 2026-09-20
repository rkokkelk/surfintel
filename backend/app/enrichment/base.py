"""EnrichmentModule interface. Modules run synchronously, in a fixed order
(see pipeline.ENRICHMENT_MODULES), each writing its own item_enrichment row.
A module that depends on another's output (KevChecker on CveExtractor) reads
it from `prior_results` — the in-memory results of modules that already ran
in this same pass — rather than querying the database, keeping the pipeline
a plain, orderable list of functions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.item import Item


class EnrichmentModule(ABC):
    name: str
    version: str = "1"

    @abstractmethod
    def run(self, item: Item, prior_results: dict[str, dict]) -> dict:
        """Return the data to persist in item_enrichment.data for this item."""
        raise NotImplementedError

    def match_fields(self, data: dict) -> dict:
        """Map this module's stored `data` onto flat alert match-view fields
        (see app/alerting/match_view.py). Default: contributes nothing."""
        return {}
