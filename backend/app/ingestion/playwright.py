import hashlib

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from app.core.media import SCREENSHOT_DIR, screenshot_path
from app.ingestion.base import FetchBackend, FetchResult

_USER_AGENT = "SurfIntelBot/0.1 (+https://github.com/surf/surfintel)"


class PlaywrightBackend(FetchBackend):
    """Headless-browser fetch: renders the page (so JS-heavy advisory pages
    work, unlike HttpFetchBackend) and takes a screenshot in the same page
    load, since loading it twice would be wasteful.
    """

    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self._timeout = timeout_seconds

    def fetch(self, item_id: str, url: str, config: dict) -> FetchResult:
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, timeout=self._timeout * 1000)

            raw_html = page.content()
            page.screenshot(path=screenshot_path(item_id), full_page=True)
            browser.close()

        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        extracted_text = " ".join(soup.get_text(separator=" ").split())
        content_hash = hashlib.sha256(extracted_text.encode()).hexdigest()

        return FetchResult(raw_html=raw_html, extracted_text=extracted_text, content_hash=content_hash, screenshot=True)