from loguru import logger
from sqlalchemy import select

from app.db.session import Session
from app.models.source import Source

def setup_log_sources(db: Session) -> None:
    """ Ensure that each source has appropriate log handlers

    :param db: DB connection
    """
    sources = db.scalars(select(Source)).all()

    for source in sources:
        log_file = 
        name = source.clean_name()
        logger.add(
            f"source_{name}.log", 
            filter=lambda record: record['extra']['source'] == source.id,
            enqueue=True,
            rotation="1 week",
            retention=7,
            compression='gz'
        )

