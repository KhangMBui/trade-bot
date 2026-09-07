from __future__ import annotations

from ..api.etrade_client import ETradeClient
from ..models.portfolio import PortfolioSnapshot
from ..storage.repositories import PortfolioRepository
from ..analytics.portfolio import PortfolioAnalysis, analyze_portfolio

def sync_portfolio(
    client: ETradeClient,
    repository: PortfolioRepository,
    account_id_key: str,
) -> PortfolioSnapshot:
    """Fetch the current E*TRADE portfolio and persist one snapshot."""
    snapshot = client.get_portfolio_snapshot(account_id_key)
    repository.save_snapshot(snapshot)
    return snapshot


def get_latest_portfolio(
    repository: PortfolioRepository,
    account_id_key: str | None = None,
) -> PortfolioSnapshot | None:
    """Load the latest persisted portfolio for analytics or agent tools."""
    return repository.get_latest_snapshot(account_id_key)

def analyze_latest_portfolio(
    repository: PortfolioRepository,
    account_id_key: str | None = None,
) -> PortfolioAnalysis | None:
    """Analyze the latest locally stored portfolio snapshot."""
    snapshot = get_latest_portfolio(repository, account_id_key)

    if snapshot is None:
        return None

    return analyze_portfolio(snapshot)
