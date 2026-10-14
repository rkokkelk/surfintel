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

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class FetchResult:
    raw_html: str
    extracted_text: str
    content_hash: str
    screenshot: bool

class FetchBackend(ABC):
    @abstractmethod
    def fetch(self, item_id: str, url: str, config: dict) -> FetchResult:
        raise NotImplementedError