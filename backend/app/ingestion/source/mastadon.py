import datetime as dt

import httpx
from httpx_auth import OAuth2AuthorizationCode

from app.ingestion.source.base import DiscoveredLink, SourceConnector


class GithubSource(SourceConnector):

    CONFIG = """
        {
            "server-url": "",
            "client-id": "",
            "client-secret": ""
            "mastadon-id": ""
        }
    """

    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self._timeout = timeout_seconds
        self.url = 'https://api.github.com/repos'
        self.headers = {
            'X-Github-Api-Version': '2026-03-10'
        }

    def discover(self, config: dict) -> list[DiscoveredLink]:
        statusses = []
        account = config.get('mastadon-id')
        url = config.get('server-url').rstrip('/')

        oauth = OAuth2AuthorizationCode(
            authorization_url=f'{url}/oauth/authorize',
            token_url=f'{url}/oauth/token',
            client_id=config.get('client-id'),
            client_secret=config.get('client-secret')
        )

        with httpx.Client() as client:
            client.get(f"{url}/api/v1/accounts/{account}/statuses", auth=oauth)

        response = httpx.get(url, headers=self.headers)
        response.raise_for_status()

        for status in response.json():
            statusses.append(
                DiscoveredLink(
                    url=status['url'],
                    title=f"@{status['account']['username']} - {status['id']}",
                    description=status['content'],
                    published_at=dt.datetime.fromisoformat(status['created_at'])
                )
            )

        return statusses