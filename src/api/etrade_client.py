from dataclasses import dataclass
from typing import Any

from requests_oauthlib import OAuth1Session

from ..models.account import Account, AccountList
from ..models.portfolio import PortfolioSnapshot


@dataclass(frozen=True)
class ETradeCredentials:
    consumer_key: str
    consumer_secret: str
    access_token: str
    access_token_secret: str


class ETradeClient:
    """Read-only E*TRADE API client for account and portfolio data."""

    BASE_URL = "https://api.etrade.com"

    def __init__(self, credentials: ETradeCredentials, timeout: float = 30.0):
        self._credentials = credentials
        self._timeout = timeout

    def _session(self) -> OAuth1Session:
        credentials = self._credentials
        return OAuth1Session(
            credentials.consumer_key,
            client_secret=credentials.consumer_secret,
            resource_owner_key=credentials.access_token,
            resource_owner_secret=credentials.access_token_secret,
        )

    def list_accounts(self) -> dict[str, Any]:
        response = self._session().get(
            f"{self.BASE_URL}/v1/accounts/list.json",
            headers={"Accept": "application/json"},
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()

    def list_account_models(self) -> list[Account]:
        """Return normalized account models for application use."""
        return AccountList.from_etrade_payload(self.list_accounts()).accounts

    def get_portfolio(self, account_id_key: str) -> dict[str, Any]:
        response = self._session().get(
            f"{self.BASE_URL}/v1/accounts/{account_id_key}/portfolio",
            params={
                "totalsRequired": "true",
                "view": "COMPLETE",
                "marketSession": "REGULAR",
            },
            headers={"Accept": "application/json"},
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_portfolio_snapshot(self, account_id_key: str) -> PortfolioSnapshot:
        """Return a normalized portfolio snapshot for an account."""
        return PortfolioSnapshot.from_etrade_payload(
            self.get_portfolio(account_id_key),
            account_id_key,
        )
