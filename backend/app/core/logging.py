import os
from pathlib import Path

from loguru import logger
from sqlalchemy import select

from app.core.config import settings
from app.db.session import Session
from app.models.source import Source

log_dir: Path = Path(settings.log_dir)
CHUNK_SIZE = 64 * 1024  # bytes read per seek-step; larger = fewer syscalls
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level:<4.4}</level> | "
    "<yellow>{extra[item]!s:<8.8}</yellow> - "
    "<level>{message}</level>"
)

def setup_log_sources(db: Session) -> None:
    """ Ensure that each source has appropriate log handlers

    :param db: DB connection
    """
    logger.configure(extra={'source': '', 'item': 'source'})

    if not log_dir.exists():
        log_dir.mkdir(parents=True)

    sources = db.scalars(select(Source)).all()

    for source in sources:
        name = source.clean_name()
        log_file = log_dir / f"source_{name}.log"

        logger.add(
            log_file,
            format=LOG_FORMAT,
            filter=lambda record, id=source.id: record['extra'].get('source') == id,
            enqueue=True,
            rotation="1 week",
            retention=7,
            compression='gz',
            colorize=True
        )

def fetch_logs(source: Source, last: int=500) -> str:
    """ Get logs for a given source
    
    :param Source: source to get logs for
    :param last: num of last lines to fetch
    :return: logs
    """
    name = source.clean_name()
    log_file = log_dir / f"source_{name}.log"

    if last == 0:
        with log_file.open('r') as f:
            return f.readlines()

    else:
        return _tail_lines(log_file, last)

def _tail_lines(path: Path, n: int, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Return the last `n` lines of `path`, reading backwards from the end.

    Only the tail of the file is read, so runtime is independent of total
    file size (works fine on multi-GB logs).
    """

    with path.open("rb") as f:
        f.seek(0, os.SEEK_END)
        remaining = f.tell()
        data = b""

        while remaining > 0:
            step = min(chunk_size, remaining)
            f.seek(remaining - step)
            data = f.read(step) + data

            # Stop as soon as we have more than n newlines.
            if data.count(b"\n") > n:
                break

            remaining -= step

    # Edge case: file without a trailing newline still yields its last line.
    lines = data.split(b"\n")
    # Empty string after trailing newline is not a line.
    if lines and lines[-1] == b"":
        lines.pop()

    result = [ln.decode("utf-8", errors="replace") for ln in lines[-n:]]
    return "\n".join(result)