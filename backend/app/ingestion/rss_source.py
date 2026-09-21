import datetime as dt

import feedparser

from app.ingestion.base import DiscoveredLink, SourceConnector


class RssSourceConnector(SourceConnector):
    """config = {"feed_url": "https://example.com/feed.xml"}"""

    def discover(self, config: dict) -> list[DiscoveredLink]:
        feed_url = config["feed_url"]
        parsed = feedparser.parse(feed_url)

        links: list[DiscoveredLink] = []
        for entry in parsed.entries:
            url = entry.get("link")
            if not url:
                continue
            links.append(
                DiscoveredLink(
                    url=url,
                    title=entry.get("title"),
                    description=entry.get("description"),
                    published_at=_parse_published(entry),
                )
            )
        return links


def _parse_published(entry) -> dt.datetime | None:
    parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed_time:
        return None
    return dt.datetime(*parsed_time[:6], tzinfo=dt.UTC)
