from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown

from app.core import logging
from app.db.session import SessionLocal, engine

app = Celery(
    __name__,
    broker_url="redis://127.0.0.1:6379/0",
    result_backend="redis://127.0.0.1:6379/0",
    timezone="Europe/Amsterdam",
    enable_utc=True,
    task_acks_late=True,
    prefetch_multiplier=1,
    task_time_limit=300,
    singleton_lock_expiry=3600,
    # There's no `singleton_json_encoder_class` config key — celery_singleton
    # (0.3.1, the current latest) hardcodes json.dumps() with no `cls=` hook
    # at all, so this was never read. Every singleton task here is called
    # with uuid.UUID args, which crashes that hardcoded call. Fixed instead
    # by using app.core.singleton_task.UuidSafeSingleton as the task base
    # (see its docstring) rather than celery_singleton.Singleton directly.
)

# Default related_name is "tasks" — Celery looks for app/ingestion/tasks.py,
# app/enrichment/tasks.py, etc. Your task lives in pipeline.py, not tasks.py,
# so without this override autodiscover finds nothing in any of these
# packages (silently — no error, just an empty [tasks] list on the worker).
app.autodiscover_tasks(["app.ingestion", "app.enrichment", "app.alerting", "app.refreshing"])


@worker_process_init.connect
def init_worker(**kwargs):
    # Each forked worker child inherits the parent's already-open DB
    # connections via fork() (the engine/pool is created at import time, in
    # the parent, before Celery forks) — reused from two processes at once,
    # they corrupt (psycopg.ProgrammingError: can't change 'autocommit' now:
    # connection in transaction status INTRANS, or "server closed the
    # connection unexpectedly"). That exception was happening right here,
    # and Celery only logs a signal handler's exception rather than crashing
    # the worker on it, so this function aborted before ever reaching the
    # `app.conf['dbSession'] = ...` line below — every task then failed with
    # KeyError('dbSession'), which is what actually surfaced, not the DB
    # error itself. Disposing first forces each child to open its own fresh
    # connections instead of reusing the parent's.
    engine.dispose()

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