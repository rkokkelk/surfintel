import uuid

from celery import signature
from loguru import logger
from sqlalchemy import select

from app.celery import app
from app.enrichment.ai_categorizer import AiCategorizer
from app.enrichment.base import EnrichmentModule
from app.enrichment.cpe_extractor import CpeExtractor
from app.enrichment.cve_extractor import CveExtractor
from app.enrichment.kev_checker import KevChecker
from app.models.enrichment import ItemEnrichment
from app.models.item import Item
from app.models.source import Source

# Fixed execution order: kev_checker depends on cve_extractor having already
# produced this item's cve_ids in this same pass.
ENRICHMENT_MODULES: dict[str, EnrichmentModule] = {
    'enrich_cve': CveExtractor(),
    'enrich_cpe': CpeExtractor(),
    'enrich_kev': KevChecker(),
    'enrich_ai': AiCategorizer()
}

def get_enrichments_tasks(item: Item, source: Source) -> list[signature]:
    tasks = []

    for name in ENRICHMENT_MODULES:
        if getattr(source, name):
            tasks.append(run_enrichment_for_item.s(item.id, name))

    return tasks


@app.task
def run_enrichment_for_item(item_id: uuid.UUID, enrichment_module: str) -> dict:
    """Run every registered module that is enabled for the item's source,
    upserting its item_enrichment row. Returns {module_name: data} for use by
    the alert matching step that follows. A module switched off on the source
    is skipped — rows it wrote earlier are left as they are.

    kev_checker reads cve_extractor's output, so with CVE extraction off it
    finds no CVE ids and reports nothing.
    """
    with app.conf['dbSession']() as db:

        item = db.get(Item, item_id)
        log = logger.bind(source=item.source_id, item=item.id)
        module = ENRICHMENT_MODULES[enrichment_module]
        log.info("Starting enrichment: {}", enrichment_module)
        data = module.run(item, db)

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

        db.commit()

    # module.name (not the toggle key): notify() feeds these to build_match_view,
    # which looks results up by module.name.
    return (module.name, data)
