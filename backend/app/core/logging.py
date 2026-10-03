from pathlib import Path

from loguru import logger
from sqlalchemy import select

from app.core.config import settings
from app.db.session import Session
from app.models.source import Source

log_dir: Path = Path(settings.log_dir)

def setup_log_sources(db: Session) -> None:
    """ Ensure that each source has appropriate log handlers

    :param db: DB connection
    """
    if not log_dir.exists():
        log_dir.mkdir(parents=True)

    sources = db.scalars(select(Source)).all()

    for source in sources:
        name = source.clean_name()
        log_file = log_dir / f"source_{name}.log"

        logger.add(
            log_file,
            filter=lambda record, id=source.id: record['extra']['source'] == id,
            enqueue=True,
            rotation="1 week",
            retention=7,
            compression='gz'
        )

