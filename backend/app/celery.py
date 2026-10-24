from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from celery_singleton import clear_locks

from app.core import logging
from app.core.config import settings
from app.db.session import SessionLocal, engine

app = Celery(
    __name__,
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,
    redbeat_redis_url=settings.celery_beat_url,
    beat_scheduler="redbeat.RedBeatScheduler",
    timezone="Europe/Amsterdam",
    enable_utc=True,
    task_acks_late=False,
    prefetch_multiplier=1,
    task_time_limit=300,
    singleton_lock_expiry=330,
)

app.autodiscover_tasks(["app.ingestion", "app.enrichment", "app.alerting", "app.refreshing"])


@worker_process_init.connect
def init_worker(**kwargs):
    # Disposing forces each child to open its own fresh connections instead of reusing the parent's.
    engine.dispose()

    # Clear all 'old' existing Celery singleton locks
    clear_locks(app)

    # Set this before the (less essential) logging setup below, so a future
    # hiccup there can't silently leave every task on this worker permanently
    # broken for its whole lifetime the way the dispose() bug above did.
    app.conf['dbSession'] = SessionLocal

    with SessionLocal() as db:
        logging.setup_log_sources(db)


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    dbSession = SessionLocal

    if dbSession:
        print('Closing database connectionn for worker.')