from __future__ import annotations

from ...analytics.portfolio import PortfolioAnalysis, analyze_portfolio
from ...config import settings
from ...storage.repositories import PortfolioRepository

def get_current_portfolio_analysis() -> PortfolioAnalysis:
  """
  Read and analyze the latest locally stored portfolio.

  This tool does not contact E*TRADE and cannot place trades.
  """
  repository = PortfolioRepository(settings.DATABASE_PATH)

  snapshot = repository.get_latest_snapshot(
    account_id_key=settings.ACCOUNT_ID_KEY,
  )

  if snapshot is None:
    raise RuntimeError(
      "No saved portfolio snapshot exists. "
      "Run `sync-portfolio` before analyzing."
    )

  return analyze_portfolio(snapshot)