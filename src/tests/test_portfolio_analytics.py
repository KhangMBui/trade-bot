from decimal import Decimal

from src.analytics.portfolio import analyze_portfolio
from src.models.portfolio import (
    PortfolioSnapshot,
    PortfolioTotals,
    Position,
    Product,
    QuoteDetails,
)


def make_snapshot() -> PortfolioSnapshot:
  return PortfolioSnapshot(
    account_id_key="account-key",
    totals=PortfolioTotals(
      total_market_value=Decimal("10000"),
      cash_balance=Decimal("500"),
      total_gain_loss=Decimal("1200"),
      total_gain_loss_pct=Decimal("13.64"),
    ),
    positions=[
      Position(
        position_id=1,
        quantity=Decimal("10"),
        market_value=Decimal("7000"),
        total_cost=Decimal("6000"),
        total_gain=Decimal("1000"),
        total_gain_pct=Decimal("16.67"),
        product=Product(symbol="VTI"),
        quote=QuoteDetails(
          price=Decimal("700"),
          currency="USD",
        ),
      ),
      Position(
        position_id=2,
        quantity=Decimal("10"),
        market_value=Decimal("3000"),
        total_cost=Decimal("2800"),
        total_gain=Decimal("200"),
        total_gain_pct=Decimal("7.14"),
        product=Product(symbol="KO"),
        quote=QuoteDetails(
          price=Decimal("300"),
          currency="USD",
        ),
      ),
    ],
  )


def test_calculates_position_weights() -> None:
  analysis = analyze_portfolio(make_snapshot())

  assert analysis.position_count == 2
  assert analysis.positions[0].symbol == "VTI"
  assert analysis.positions[0].portfolio_weight == Decimal("0.7")
  assert analysis.positions[1].portfolio_weight == Decimal("0.3")


def test_calculates_cash_weight() -> None:
  analysis = analyze_portfolio(make_snapshot())

  assert analysis.cash_weight == Decimal("0.05")


def test_identifies_largest_position() -> None:
  analysis = analyze_portfolio(make_snapshot())

  assert analysis.largest_position is not None
  assert analysis.largest_position.symbol == "VTI"
  assert analysis.largest_position.portfolio_weight == Decimal("0.7")


def test_flags_position_over_limit() -> None:
  analysis = analyze_portfolio(
    make_snapshot(),
    max_single_position_weight=Decimal("0.50"),
  )

  assert "VTI: Position exceeds 50% portfolio limit" in analysis.risk_flags


def test_flags_low_cash() -> None:
  snapshot = make_snapshot()
  snapshot.totals.cash_balance = Decimal("100")

  analysis = analyze_portfolio(
    snapshot,
    minimum_cash_weight=Decimal("0.05"),
  )

  assert "Cash is below 5% minimum" in analysis.risk_flags


def test_missing_market_value_does_not_crash() -> None:
  snapshot = make_snapshot()
  snapshot.positions[0].market_value = None

  analysis = analyze_portfolio(snapshot)

  position = analysis.positions[0]

  assert position.portfolio_weight is None
  assert "Missing market value" in position.risk_flags