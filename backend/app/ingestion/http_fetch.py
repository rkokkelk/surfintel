import hashlib

import httpx
from bs4 import BeautifulSoup

from app.ingestion.base import FetchBackend, FetchResult

_USER_AGENT = "SurfIntelBot/0.1 (+https://github.com/surf/surfintel)"


class HttpFetchBackend(FetchBackend):
    """Direct HTTP fetch + naive content extraction. Good enough for plain
    HTML advisory/news pages; a JS-rendering backend (e.g. changedetection.io)
    can be added later for pages that need it, behind the same interface.
    """

    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self._timeout = timeout_seconds

    def fetch(self, item_id: str, url: str, config: dict) -> FetchResult:
        # item_id/config unused here — this backend never screenshots; kept
        # in the signature for interface parity with PlaywrightBackend.
        response = httpx.get(url, timeout=self._timeout, headers={"User-Agent": _USER_AGENT}, follow_redirects=True)
        response.raise_for_status()
        raw_html = response.text

        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        extracted_text = " ".join(soup.get_text(separator=" ").split())

        content_hash = hashlib.sha256(extracted_text.encode()).hexdigest()
        return FetchResult(raw_html=raw_html, extracted_text=extracted_text, content_hash=content_hash, screenshot=False)