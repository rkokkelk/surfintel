"""Ties the whole ingestion pipeline together for one polling cycle:
Source -> discover links -> Item -> fetch -> enrich -> evaluate alerts.
Invoked by app/cli.py (`surfintel run-ingestion`), e.g. from cron.
"""

import uuid

from celery import Celery, chord, group
from loguru import logger
from sqlalchemy import select

from app.alerting.tasks import notify
from app.celery import app
from app.enrichment.tasks import run_enrichment_for_item
from app.models.cve import ItemCve
from app.models.item import Item
from app.models.source import Source

PERIOD = 1800

@app.on_after_finalize.connect
def setup_refresh_tasks(sender: Celery, **kwargs):
    """ Setup periodic refresh items task
    """
    periodic_refereshment_task = periodic_refresh_items.s()
    sender.add_periodic_task(PERIOD, periodic_refereshment_task, name=f"periodic_refresh")
    periodic_refereshment_task.delay()

@app.task
def periodic_refresh_items() -> None:
    """ Periodic tasks to start refreshments of relevant items

    Ensure that refresh tasks are scatterd during entire PERIOD
    """
    with app.conf['dbSession']() as db:

        item_ids = set(db.scalars(select(Item.id).where(ItemCve.item_id == Item.id)).all())
        logger.info("Starting refresh on: %d items!", len(item_ids))

        step = PERIOD / len(item_ids)
        tasks = group(refresh_item.s(item_id) for item_id in item_ids)
        tasks.skew(start=1, stop=PERIOD, step=step)()

@app.task
def refresh_item(item_id: uuid.UUID):
    with app.conf['dbSession']() as db:
        item = db.get(Item, item_id)
        source = db.get(Source, item.source_id)
        log = logger.bind(source=source.id, item=item.id)

        log.info("refresh item")
        refresh_tasks = [run_enrichment_for_item.s(item.id, 'enrich_cve')]
        chord(refresh_tasks, notify.s(item_id=item.id, source_id=source.id))()