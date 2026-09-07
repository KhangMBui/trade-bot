from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..models.portfolio import PortfolioSnapshot, Position

class PositionAnalysis(BaseModel):
  """Analytics calculated for one portfolio position."""

  model_config = ConfigDict(extra="forbid")

  symbol: str
  quantity: Decimal | None = None
  market_value: Decimal | None = None
  portfolio_weight: Decimal | None = None
  total_gain: Decimal | None = None
  total_gain_pct: Decimal | None = None
  current_price: Decimal | None = None
  risk_flags: list[str] = Field(default_factory=list)

class PortfolioAnalysis(BaseModel):
  """Deterministic portfolio analytics consumed by reports and agents."""

  model_config = ConfigDict(extra="forbid")

  account_id_key: str
  analyzed_at: str
  total_market_value: Decimal | None = None
  cash_balance: Decimal | None = None
  cash_weight: Decimal | None = None
  total_gain_loss: Decimal | None = None
  total_gain_loss_pct: Decimal | None = None
  position_count: int
  largest_position: PositionAnalysis | None = None
  positions: list[PositionAnalysis]
  risk_flags: list[str] = Field(default_factory=list)

def analyze_portfolio(
    snapshot: PortfolioSnapshot,
    *,
    max_single_position_weight: Decimal = Decimal("0.10"),
    minimum_cash_weight: Decimal = Decimal("0.05"),
) -> PortfolioAnalysis:
  """
  Analyze a typed portfolio snapshot.

  This function is deterministic. It does not call an LLM,
  E*TRADE, or any other external service.
  """
  totals = snapshot.totals

  denominator = _portfolio_denominator(snapshot)

  analyzed_positions = [
    _analyze_position(
      position,
      denominator=denominator,
      max_single_position_weight=max_single_position_weight,
    )
    for position in snapshot.positions if position.symbol
  ]

  largest_position = _largest_position(analyzed_positions)
  risk_flags = _portfolio_risk_flags(
    analyzed_positions=analyzed_positions,
    cash_balance=totals.cash_balance,
    cash_weight=_weight(totals.cash_balance, denominator),
    minimum_cash_weight=minimum_cash_weight,
  )

  return PortfolioAnalysis(
    account_id_key=snapshot.account_id_key,
    analyzed_at=snapshot.retrieved_at.isoformat(),
    total_market_value=totals.total_market_value,
    cash_balance=totals.cash_balance,
    cash_weight=_weight(totals.cash_balance, denominator),
    total_gain_loss=totals.total_gain_loss,
    total_gain_loss_pct=totals.total_gain_loss_pct,
    position_count=len(analyzed_positions),
    largest_position=largest_position,
    positions=analyzed_positions,
    risk_flags=risk_flags,
  )

def _portfolio_denominator(snapshot: PortfolioSnapshot) -> Decimal | None:
  """
  Select the denominator used for portfolio weights.

  E*TRADE's totalMarketValue is preferred. If unavailable,
  the sum of position market values is used.
  """
  if snapshot.totals.total_market_value is not None:
      return snapshot.totals.total_market_value

  position_values = [
      position.market_value
      for position in snapshot.positions
      if position.market_value is not None
  ]

  if not position_values:
      return None

  return sum(position_values, Decimal("0"))

def _analyze_position(
  position: Position,
  *,
  denominator: Decimal | None,
  max_single_position_weight: Decimal,
) -> PortfolioAnalysis:
  symbol = position.symbol or "UNKNOWN"
  weight = _weight(position.market_value, denominator)

  risk_flags: list[str] = []

  if weight is not None and weight > max_single_position_weight:
    risk_flags.append(
      f"Position exceeds {max_single_position_weight:.0%} portfolio limit"
    )

  if position.market_value is None:
    risk_flags.append("Missing market value")

  if position.quantity is None:
    risk_flags.append("Missing quantity")

  if position.current_price is None:
    risk_flags.append("Missing current price")

  return PositionAnalysis(
    symbol=symbol,
    quantity=position.quantity,
    market_value=position.market_value,
    portfolio_weight=weight,
    total_gain=position.total_gain,
    total_gain_pct=position.total_gain_pct,
    current_price=position.current_price,
    risk_flags=risk_flags,
  )

def _portfolio_risk_flags(
    *,
    analyzed_positions: list[PositionAnalysis],
    cash_balance: Decimal | None,
    cash_weight: Decimal | None,
    minimum_cash_weight: Decimal,
) -> list[str]:
  flags: list[str] = []

  if not analyzed_positions:
    flags.append("Portfolio has no analyzable positions")

  if cash_balance is None:
    flags.append("Cash balance is unavailable")
  elif cash_weight is not None and cash_weight < minimum_cash_weight:
    flags.append(
      f"Cash is below {minimum_cash_weight:.0%} minimum"
    )

  for position in analyzed_positions:
    for flag in position.risk_flags:
      flags.append(f"{position.symbol}: {flag}")
  return flags

def _largest_position(
    positions: list[PositionAnalysis]
) -> PositionAnalysis | None:
  positions_with_weights = [
    position for position in positions if position.portfolio_weight is not None
  ]

  if not positions_with_weights:
    return None

  return max(
    positions_with_weights,
    key=lambda position: position.portfolio_weight or Decimal("0"),
  )

def _weight(
    numerator: Decimal | None,
    denominator: Decimal | None,
) -> Decimal | None:
  if numerator is None or denominator is None or denominator <= 0:
    return None

  return numerator / denominator