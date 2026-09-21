"""Where generated media (currently: item screenshots) lives on disk.

Shared between the writer (app/ingestion/playwright.py) and the reader
(the /items/{id}/screenshot route) so the path format can't drift between
the two — that mismatch (missing .png, wrong path) was a real bug once.
"""

import uuid
from pathlib import Path

MEDIA_DIR = Path("media")
SCREENSHOT_DIR = MEDIA_DIR / "screenshots"


def screenshot_path(item_id: str | uuid.UUID) -> Path:
    return SCREENSHOT_DIR / f"{item_id!s}.png"
