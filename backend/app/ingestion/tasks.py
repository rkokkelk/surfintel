"""Ties the whole ingestion pipeline together for one polling cycle:
Source -> discover links -> Item -> fetch -> enrich -> evaluate alerts.
Invoked by app/cli.py (`surfintel run-ingestion`), e.g. from cron.
"""

import logging
import datetime as dt

import uuid
from enum import Enum

from sqlalchemy import select
from sqlalchemy.orm import Session

from celery import group, chord, Celery

from app.celery import app
from app.db.session import SessionLocal
from app.ingestion.http_fetch import HttpFetchBackend
from app.ingestion.playwright import PlaywrightBackend
from app.alerting.tasks import notify
from app.enrichment.tasks import get_enrichments_tasks
from app.ingestion.base import FetchBackend, SourceConnector
from app.ingestion.rss_source import RssSourceConnector
from app.ingestion.html_source import HTMLSourceConnector
from app.models.item import Item, ItemStatus
from app.models.source import Source, SourceType

CONNECTORS: dict[SourceType, SourceConnector] = {
    SourceType.rss: RssSourceConnector(),
    SourceType.html: HTMLSourceConnector(),
    # SourceType.custom_module: resolved per-source via config["module"] once
    # the first custom module (e.g. a changedetection.io-backed connector) is
    # built — deliberately not implemented yet.
}

class FETCH_TYPES(Enum):
    HTTPX = HttpFetchBackend
    PLAYWRIGHT = PlaywrightBackend

logger = logging.getLogger(__name__)

@app.on_after_finalize.connect
def setup_source_periodic_tasks(sender: Celery, **kwargs):
    with SessionLocal() as db:
        sources = db.scalars(select(Source))

        for source in sources:
            source_signature = run_ingestion_cycle.s(source.id, fetch_identifier=FETCH_TYPES.PLAYWRIGHT.name)

            logger.info("Setting up periodic tasks: %s - %ds ", source.name, source.poll_interval_seconds)
            sender.add_periodic_task(source.poll_interval_seconds, source_signature, name=f"periodic_{source.id}")

            logger.info("Trigger initial lookup: %s ", source.name)
            source_signature.delay()

@app.task
def run_ingestion_cycle(source_id: uuid.UUID, fetch_identifier: str | None = FETCH_TYPES.HTTPX, force: bool = False) -> None:
    """ Start Ingestion cycle
    
    :param Session: DB session
    :param fetch_backend: FetchBackend to gather items via 
    :param source: Source to limit ingestion on if given
    :param force: Whether to gather all items, even if they are also gathered
    """
    # get_db() is a FastAPI dependency generator (`yield`) — calling it directly
    # returns the generator object itself, not a Session; that only works via
    # Depends(), which doesn't apply here since this runs in a Celery worker,
    # outside any request. Open/close a session the same way app/cli.py does.
    with app.conf['dbSession']() as db:
        source = db.get(Source, source_id) if source_id else None
        sources = [source] if source else db.scalars(select(Source).where(Source.enabled.is_(True))).all()

        for entry in sources:
            poll_source(db, entry)
            entry.last_polled_at = dt.datetime.now(dt.UTC)
            db.commit()

        if force:
            pending_items = db.scalars(select(Item)).all()
        else:
            pending_items = db.scalars(select(Item).where(Item.status == ItemStatus.discovered)).all()

        # Start paralell fetching tasks
        group_task = group(fetch_discovered_item.s(item.id, source.id, fetch_identifier=fetch_identifier) for item in pending_items)
        group_task()  


def poll_source(db: Session, source: Source) -> None:
    """ Get all the newly discovered itesm from the source
    :param Session: DB session
    :param source: Source
    """
    connector = CONNECTORS.get(source.type)
    if connector is None:
        return

    logger.info("Starting discovery %s: %s", source.name, source.config)
    links = connector.discover(source.config)
    logger.debug("Identified %s: %d links", source.name, len(links))

    for link in links:
        existing = db.scalar(select(Item).where(Item.url == link.url))
        if existing:
            continue
        db.add(
            Item(
                source_id=source.id,
                url=link.url,
                title=link.title,
                description=link.description,
                published_at=link.published_at,
                status=ItemStatus.discovered,
            )
        )

@app.task
def fetch_discovered_item(item_id: uuid.UUID, source_id: uuid.UUID, fetch_identifier: str | None = FETCH_TYPES.HTTPX):
    with app.conf['dbSession']() as db:
        fetch_backend = FETCH_TYPES[fetch_identifier].value()
        item = db.get(Item, item_id)
        source = db.get(Source, source_id)

        try:
            logger.debug("Parsed[%s]: %s", item.id, item.url)
            result = fetch_backend.fetch(item.id, item.url, item.source.config)

            now = dt.datetime.now(dt.UTC)
            if item.content_hash != result.content_hash:
                item.last_changed_at = now
            item.raw_html = result.raw_html
            item.extracted_text = result.extracted_text
            item.content_hash = result.content_hash
            item.last_checked_at = now
            item.status = ItemStatus.fetched

            # Commit *before* dispatching: the enrichment tasks run in other worker
            # processes and read item.extracted_text from the database. The commit in
            # `finally` below only happens after the chord has been sent, so without this
            # they can start before the fetched content is visible.
            db.commit()

            # Start enrichment tasks and finally notify
            chord(get_enrichments_tasks(item, source), notify.s(item_id=item.id, source_id=source.id))()

        except Exception as e:  # noqa: BLE001
            logger.warning("Fetching failed %s [%s] --> %s: %s", source.name, item.id, item.url, e)
            item.status = ItemStatus.error

        finally:
            db.commit()