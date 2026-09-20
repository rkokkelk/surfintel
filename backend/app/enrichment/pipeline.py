from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enrichment.ai_categorizer import AiCategorizer
from app.enrichment.base import EnrichmentModule
from app.enrichment.cpe_extractor import CpeExtractor
from app.enrichment.cve_extractor import CveExtractor
from app.enrichment.kev_checker import KevChecker
from app.models.enrichment import ItemEnrichment
from app.models.item import Item

# Fixed execution order: kev_checker depends on cve_extractor having already
# produced this item's cve_ids in this same pass.
ENRICHMENT_MODULES: list[EnrichmentModule] = [
    CveExtractor(),
    CpeExtractor(),
    KevChecker(),
    AiCategorizer(),
]


def run_enrichment_for_item(db: Session, item: Item) -> dict[str, dict]:
    """Run every registered module against `item`, upserting its
    item_enrichment row. Returns {module_name: data} for use by the alert
    matching step that follows.
    """
    results: dict[str, dict] = {}

    for module in ENRICHMENT_MODULES:
        data = module.run(item, results)
        results[module.name] = data

        existing = db.scalar(
            select(ItemEnrichment).where(
                ItemEnrichment.item_id == item.id, ItemEnrichment.module_name == module.name
            )
        )
        if existing:
            existing.data = data
            existing.module_version = module.version
        else:
            db.add(
                ItemEnrichment(
                    item_id=item.id, module_name=module.name, module_version=module.version, data=data
                )
            )

    return results
