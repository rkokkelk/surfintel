"""Ties the whole ingestion pipeline together for one polling cycle:
Source -> discover links -> Item -> fetch -> enrich -> evaluate alerts.
Invoked by app/cli.py (`surfintel run-ingestion`), e.g. from cron.
"""

import datetime as dt
import random
import uuid
from enum import Enum

from celery import Celery, chord, group
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.alerting.tasks import notify
from app.celery import app
from app.core.singleton_task import UuidSafeSingleton
from app.db.session import SessionLocal
from app.enrichment.tasks import get_enrichments_tasks
from app.ingestion.base import SourceConnector
from app.ingestion.http_fetch import HttpFetchBackend
from app.ingestion.playwright import PlaywrightBackend
from app.ingestion.source import GithubSource, HTMLSourceConnector, RssSourceConnector
from app.models.item import Item, ItemStatus
from app.models.source import Source, SourceType

CONNECTORS: dict[SourceType, SourceConnector] = {
    SourceType.rss: RssSourceConnector(),
    SourceType.html: HTMLSourceConnector(),
    SourceType.gh: GithubSource(),
    # SourceType.custom_module: resolved per-source via config["module"] once
    # the first custom module (e.g. a changedetection.io-backed connector) is
    # built — deliberately not implemented yet.
}

class FETCH_TYPES(Enum):
    HTTPX = HttpFetchBackend
    PLAYWRIGHT = PlaywrightBackend

@app.on_after_finalize.connect
def setup_source(sender: Celery, **kwargs):
    """ Setup all periodic source tasks 
    
    Adds jitter so that not all sources are gathered simultanously
    """
    with SessionLocal() as db:
        sources = db.scalars(select(Source))

        for source in sources:
            poll = source.poll_interval_seconds
            jitter = random.randint(1, poll)

            setup_source_signature = setup_source_periodic_task.s(source.id)
            setup_source_signature.apply_async(countdown=jitter)
            logger.info("Starting run of source! (jitter={}, poll={})", jitter, poll)

@app.task(base=UuidSafeSingleton)
def setup_source_periodic_task(source_id: uuid.UUID) -> None:
    log = logger.bind(source=source_id)
    # outside any request. Open/close a session the same way app/cli.py does.
    with app.conf['dbSession']() as db:
        source = db.get(Source, source_id)

        log.success("Setting up periodic tasks: {}", source.poll_interval_seconds)
        run_source_ingestion = run_ingestion.s(source.id, fetch_identifier=FETCH_TYPES.PLAYWRIGHT.name)

        app.add_periodic_task(source.poll_interval_seconds, run_source_ingestion, name=f"periodic_{source.id}")
        run_source_ingestion()


@app.task(base=UuidSafeSingleton)
def run_ingestion(source_id: uuid.UUID, fetch_identifier: str | None = FETCH_TYPES.HTTPX, force: bool = False) -> None:
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
        log = logger.bind(source=source_id)
        source = db.get(Source, source_id)

        log.info("Starting discovery: {}", source.config)

        poll_source(db, source)
        source.last_polled_at = dt.datetime.now(dt.UTC)
        db.commit()

        stmt = select(Item).where(Item.source_id == source.id)

        if not force:
            stmt = stmt.where(Item.status == ItemStatus.discovered)

        pending_items = db.scalars(stmt).all()

        log.info("pending items (pending={})", len(pending_items))

        # Start paralell fetching tasks
        group_task = group(fetch_discovered_item.s(item.id, source.id, fetch_identifier=fetch_identifier) for item in pending_items)
        group_task.skew(start=1, step=25)()  

@app.task
def retry_failed_items(status: list[ItemStatus] = [ItemStatus.discovered, ItemStatus.error, ItemStatus.fetched], source_id: uuid.UUID | None = None) -> None:
    """ Refetch and analyse previously
    
    :param status: list of statusses to filter on
    :param source: Source list to filter
    """
    log = logger.bind(source=source_id)
    with app.conf['dbSession']() as db:
        stmt = select(Item).where(Item.status.in_(status))
        
        if source_id:
            stmt = stmt.where(Item.source_id == source_id)

        redo_items = db.scalars(stmt).all()

        # Start paralell fetching tasks
        group_task = group(fetch_discovered_item.s(item.id, item.source.id, fetch_identifier='PLAYWRIGHT') for item in redo_items)
        group_task()  


def poll_source(db: Session, source: Source) -> None:
    """ Get all the newly discovered itesm from the source
    :param Session: DB session
    :param source: Source
    """
    log = logger.bind(source=source.id)
    # outside any request. Open/close a session the same way app/cli.py does.
    connector = CONNECTORS.get(source.type)
    if connector is None:
        return

    links = connector.discover(source.config)

    new = 0
    total = len(links)

    for link in links:
        existing = db.scalar(select(Item).where(Item.url == link.url))
        if existing:
            continue
        new += 1
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

    log.info("Links: new[{}], existing[{}], total[{}]", new, total-new, total)

@app.task(base=UuidSafeSingleton, autoretry_for=(Exception,), retry_backoff=60, retry_backoff_max=3600, retry_jitter=False, max_retries=5)
def fetch_discovered_item(item_id: uuid.UUID, source_id: uuid.UUID, fetch_identifier: str | None = FETCH_TYPES.HTTPX):
    log = logger.bind(source=source_id, item=item_id)
    with app.conf['dbSession']() as db:
        fetch_backend = FETCH_TYPES[fetch_identifier].value()
        item = db.get(Item, item_id)
        source = db.get(Source, source_id)

        try:
            result = fetch_backend.fetch(item.id, item.url, item.source.config)
            log.success("fetched: {}", item.url)

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

        except Exception as e:
            log.warning("Fetching failed: {} ({})", e, item.url)
            item.status = ItemStatus.error

            db.commit()
            raise e  # noqa: TRY201
