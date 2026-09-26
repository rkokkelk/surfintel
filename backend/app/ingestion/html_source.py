import datetime as dt

from bs4 import BeautifulSoup

from playwright.sync_api import sync_playwright

from app.ingestion.base import DiscoveredLink, SourceConnector


class HTMLSourceConnector(SourceConnector):
    """config = {"feed_url": "https://example.com/feed.xml", "row_identifier":""}"""
    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self._timeout = timeout_seconds

    def discover(self, config: dict) -> list[DiscoveredLink]:
        links = []
        feed_url = config["feed_url"]

        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto(feed_url, timeout=self._timeout * 1000)

            try:
                if config.get('wait-selector'):
                    page.wait_for_selector(config['wait-selector'], state='attached')

                raw_html = page.content()
            except:
                pass
            finally:
                context.close()
                browser.close()


        soup = BeautifulSoup(raw_html, "html.parser")


        for entry in soup.select(config['row-selector']):

            title = entry.select_one(config['item']['title-selector']).text
            link = entry.select_one(config['item']['link-selector']).attrs['href']
            description = entry.select_one(config['item']['description-selector']).text

            if not link:
                continue

            links.append(
                DiscoveredLink(
                    url=link,
                    title=title,
                    description=description,
                    published_at=dt.datetime.now()
                )
            )
        return links


def _parse_published(entry) -> dt.datetime | None:
    parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed_time:
        return None
    return dt.datetime(*parsed_time[:6], tzinfo=dt.UTC)
