"""Two pluggable interfaces that make up the discovery/fetch stage of the
ingestion pipeline (see docs/architecture.md):

- SourceConnector: turns a Source's config into a list of discovered links.
  An RSS feed entry rarely has the full article, so only the link is trusted.
- FetchBackend: turns one URL into raw HTML + extracted text. The default is
  a direct HTTP fetch; a changedetection.io-backed backend (for vendor pages
  without RSS that need JS rendering or ongoing change-monitoring) can be
  added later behind the same interface without touching the pipeline.
"""

from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DiscoveredLink:
    url: str
    title: str | None = None
    description: str | None = None
    published_at: dt.datetime | None = None


@dataclass
class FetchResult:
    raw_html: str
    extracted_text: str
    content_hash: str
    screenshot: bool

class SourceConnector(ABC):
    @abstractmethod
    def discover(self, config: dict) -> list[DiscoveredLink]:
        raise NotImplementedError


class FetchBackend(ABC):
    @abstractmethod
    def fetch(self, item_id: str, url: str, config: dict) -> FetchResult:
        raise NotImplementedError