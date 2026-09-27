import datetime as dt

import httpx
from bs4 import BeautifulSoup

from playwright.sync_api import sync_playwright

from app.ingestion.base import DiscoveredLink, SourceConnector


class GithubSource(SourceConnector):
    """config = {"package": "wordpress"}"""
    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self._timeout = timeout_seconds
        self.url = 'https://api.github.com/repos'
        self.headers = {
            'X-Github-Api-Version': '2026-03-10'
        }

    def discover(self, config: dict) -> list[DiscoveredLink]:
        advisories = []
        url = f"{self.url}/{config.get('repo')}/security-advisories"

        response = httpx.get(url, headers=self.headers)
        response.raise_for_status()

        for advisory in response.json():
            advisories.append(
                DiscoveredLink(
                    url=advisory['html_url'],
                    title=advisory['summary'],
                    description=advisory['description'],
                    published_at=dt.datetime.fromisoformat(advisory['published_at'])
                )
            )
        return advisories


def _parse_published(entry) -> dt.datetime | None:
    parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed_time:
        return None
    return dt.datetime(*parsed_time[:6], tzinfo=dt.UTC)
