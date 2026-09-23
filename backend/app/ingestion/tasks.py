"""Ties the whole ingestion pipeline together for one polling cycle:
Source -> discover links -> Item -> fetch -> enrich -> evaluate alerts.
Invoked by app/cli.py (`surfintel run-ingestion`), e.g. from cron.
"""

import logging
import datetime as dt

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.celery import app
from app.ingestion.playwright import PlaywrightBackend
from app.alerting.engine import evaluate_alerts_for_item
from app.enrichment.pipeline import run_enrichment_for_item
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

logger = logging.getLogger(__name__)

@app.task
def run_ingestion_cycle(fetch_backend: FetchBackend | None = None, source_id: uuid.UUID | None = None, force: bool = False) -> None:
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
        fetch_backend = fetch_backend or PlaywrightBackend()
        sources = [source] if source else db.scalars(select(Source).where(Source.enabled.is_(True))).all()

        for entry in sources:
            _poll_source(db, entry)
            entry.last_polled_at = dt.datetime.now(dt.UTC)
            db.commit()

        if force:
            pending_items = db.scalars(select(Item)).all()
        else:
            pending_items = db.scalars(select(Item).where(Item.status == ItemStatus.discovered)).all()

        for item in pending_items:
            _fetch_and_enrich(db, item, fetch_backend)
            db.commit()


def _poll_source(db: Session, source: Source) -> None:
    connector = CONNECTORS.get(source.type)
    if connector is None:
        return

    logger.info("Starting discovery %s: %s", source.name, source.config)
    links = connector.discover(source.config)
    logger.info("Identified %d links", len(links))

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


def _fetch_and_enrich(db: Session, item: Item, fetch_backend: FetchBackend) -> None:
    try:
        logger.debug("Parsed[%s]: %s", item.id, item.url)
        result = fetch_backend.fetch(item.id, item.url, item.source.config)
    except Exception as e:  # noqa: BLE001
        logger.error(e)
        item.status = ItemStatus.error
        return

    now = dt.datetime.now(dt.UTC)
    if item.content_hash != result.content_hash:
        item.last_changed_at = now
    item.raw_html = result.raw_html
    item.extracted_text = result.extracted_text
    item.content_hash = result.content_hash
    item.last_checked_at = now
    item.status = ItemStatus.fetched

    source = db.get(Source, item.source_id)
    enrichment_results = run_enrichment_for_item(db, item)
    item.status = ItemStatus.enriched

    evaluate_alerts_for_item(db, item, source, enrichment_results)
