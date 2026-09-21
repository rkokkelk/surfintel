"""Ties the whole ingestion pipeline together for one polling cycle:
Source -> discover links -> Item -> fetch -> enrich -> evaluate alerts.
Invoked by app/cli.py (`surfintel run-ingestion`), e.g. from cron.
"""

import logging
import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.alerting.engine import evaluate_alerts_for_item
from app.enrichment.pipeline import run_enrichment_for_item
from app.ingestion.base import FetchBackend, SourceConnector
from app.ingestion.http_fetch import HttpFetchBackend
from app.ingestion.rss_source import RssSourceConnector
from app.models.item import Item, ItemStatus
from app.models.source import Source, SourceType

CONNECTORS: dict[SourceType, SourceConnector] = {
    SourceType.rss: RssSourceConnector(),
    # SourceType.custom_module: resolved per-source via config["module"] once
    # the first custom module (e.g. a changedetection.io-backed connector) is
    # built — deliberately not implemented yet.
}

logger = logging.getLogger(__name__)

def run_ingestion_cycle(db: Session, fetch_backend: FetchBackend | None = None, force: bool = False) -> None:
    fetch_backend = fetch_backend or HttpFetchBackend()

    sources = db.scalars(select(Source).where(Source.enabled.is_(True))).all()
    for source in sources:
        _poll_source(db, source)
        source.last_polled_at = dt.datetime.now(dt.UTC)
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

    for link in connector.discover(source.config):
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
