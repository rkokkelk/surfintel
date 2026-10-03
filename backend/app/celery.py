from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown

from app.core import logging
from app.db.session import SessionLocal

app = Celery(
    __name__,
    broker="redis://127.0.0.1:6379/0",
    backend="redis://127.0.0.1:6379/0"
)

# Default related_name is "tasks" — Celery looks for app/ingestion/tasks.py,
# app/enrichment/tasks.py, etc. Your task lives in pipeline.py, not tasks.py,
# so without this override autodiscover finds nothing in any of these
# packages (silently — no error, just an empty [tasks] list on the worker).
app.autodiscover_tasks(["app.ingestion", "app.enrichment", "app.alerting", "app.refreshing"])


@worker_process_init.connect
def init_worker(**kwargs):
    with SessionLocal() as db:
        logging.setup_log_sources(db)

    app.conf['dbSession'] = SessionLocal


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    dbSession = SessionLocal

    if dbSession:
        print('Closing database connectionn for worker.')