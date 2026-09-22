import datetime as dt
import enum
import httpx
import base64
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from sqlalchemy import JSON, Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPk


class SourceType(str, enum.Enum):
    rss = "rss"
    html = "html"
    custom_module = "custom_module"


class Source(Base, UUIDPk, TimestampMixin):
    """A feed to poll. `config` is interpreted by the Source implementation
    registered for `type` (e.g. {"feed_url": "..."} for rss, or
    {"module": "vendor_x_advisories", ...} for a custom module).
    """

    __tablename__ = "source"

    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[SourceType] = mapped_column(Enum(SourceType, name="source_type"))
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    favicon: Mapped[bool] = mapped_column(Text, nullable=True)
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=3600)
    last_polled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def get_favicon(self):
        """ Gather the favicon
        """
        url = self.config.get('feed_url')
        if not url:
            return

        response = httpx.get(url, timeout=15, follow_redirects=True)
        response.raise_for_status()
        raw_html = response.content

        icon_link = None
        soup = BeautifulSoup(raw_html, "html.parser")

        if soup:
            icon_link = soup.find("link", rel="shortcut icon")

        if not icon_link:
            url_parsed = urlparse(url).netloc
            domain = '.'.join(url_parsed.split('.')[-2:]) # Ensure only 2LD is used
            url = f"https://{domain}/favicon.ico"
            icon = httpx.get(url, follow_redirects=True).content
        else:
            icon = httpx.get(icon_link['href']).content
        
        self.favicon = base64.b64encode(icon).decode()


