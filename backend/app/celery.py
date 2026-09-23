import logging

from celery import Celery
from app.db.session import SessionLocal
from celery.signals import worker_process_init, worker_process_shutdown

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Celery(
    __name__,
    broker="redis://127.0.0.1:6379/0",
    backend="redis://127.0.0.1:6379/0"
)

# Default related_name is "tasks" — Celery looks for app/ingestion/tasks.py,
# app/enrichment/tasks.py, etc. Your task lives in pipeline.py, not tasks.py,
# so without this override autodiscover finds nothing in any of these
# packages (silently — no error, just an empty [tasks] list on the worker).
app.autodiscover_tasks(["app.ingestion", "app.enrichment", "app.alerting"])


@worker_process_init.connect
def init_worker(**kwargs):
    app.conf['dbSession'] = SessionLocal


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    dbSession = SessionLocal

    if dbSession:
        print('Closing database connectionn for worker.')