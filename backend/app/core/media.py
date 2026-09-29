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

    item_id = str(item_id)

    dir1 = item_id[0:2]
    dir2 = item_id[2:4]

    media_dir = SCREENSHOT_DIR / dir1 / dir2
    media_dir.mkdir(parents=True, exist_ok=True)

    return media_dir / f"{item_id!s}.png"
