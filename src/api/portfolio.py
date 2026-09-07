from typing import Any

from .etrade_client import ETradeClient


def view_portfolio(client: ETradeClient, account_id_key: str) -> dict[str, Any]:
    return client.get_portfolio(account_id_key)
