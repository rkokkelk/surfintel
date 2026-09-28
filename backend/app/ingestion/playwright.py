import hashlib

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Playwright

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

    def load_extension(self, playwright:Playwright):
        context = playwright.chromium.launch_persistent_context(
            '.',
            channel="chromium",
            args=[
                f"--disable-extensions-except=",
                f"--load-extension=",
            ],
        )
        if len(context.service_workers) == 0:
            service_worker = context.wait_for_event('serviceworker')
        else:
            service_worker = context.service_workers[0]

        # Test the service worker as you would any other worker.
        context.close()

    def fetch(self, item_id: str, url: str, config: dict) -> FetchResult:
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, timeout=self._timeout * 1000)

            if config.get('content-selector'):
                page.wait_for_selector(config['content-selector'], state='attached')
                page.locator(config['content-selector']).screenshot(path=screenshot_path(item_id))
            else:
                page.screenshot(path=screenshot_path(item_id), full_page=True)

            raw_html = page.content()
            browser.close()

        soup = BeautifulSoup(raw_html, "html.parser")

        if config.get('content-selector'):
            soup = soup.select(config['content-selector'])[0]

        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        extracted_text = " ".join(soup.get_text(separator=" ").split())
        content_hash = hashlib.sha256(extracted_text.encode()).hexdigest()

        return FetchResult(raw_html=raw_html, extracted_text=extracted_text, content_hash=content_hash, screenshot=True)