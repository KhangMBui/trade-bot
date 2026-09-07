from typing import Any

from .etrade_client import ETradeClient


def list_account(client: ETradeClient) -> dict[str, Any]:
    return client.list_accounts()
