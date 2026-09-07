from .etrade_client import ETradeClient
from ..models.portfolio import PortfolioSnapshot


def view_portfolio(
    client: ETradeClient, account_id_key: str
) -> PortfolioSnapshot:
    """Return a normalized portfolio snapshot for an account."""
    return client.get_portfolio_snapshot(account_id_key)
