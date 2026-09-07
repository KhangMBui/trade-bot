from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Product(BaseModel):
    """Security identity information returned by E*TRADE."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    symbol: str | None = None
    security_type: str | None = Field(default=None, alias="securityType")
    expiry_year: int | None = Field(default=None, alias="expiryYear")
    expiry_month: int | None = Field(default=None, alias="expiryMonth")
    expiry_day: int | None = Field(default=None, alias="expiryDay")
    strike_price: Decimal | None = Field(default=None, alias="strikePrice")
    product_id: dict[str, Any] | None = Field(default=None, alias="productId")


class QuoteDetails(BaseModel):
    """Market and risk fields returned in a complete E*TRADE position."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    price: Decimal | None = None
    adjusted_price: Decimal | None = Field(default=None, alias="adjPrice")
    change: Decimal | None = None
    change_pct: Decimal | None = Field(default=None, alias="changePct")
    previous_close: Decimal | None = Field(default=None, alias="prevClose")
    volume: int | None = None
    last_trade: Decimal | None = Field(default=None, alias="lastTrade")
    last_trade_time: int | None = Field(default=None, alias="lastTradeTime")
    adjusted_last_trade: Decimal | None = Field(default=None, alias="adjLastTrade")
    symbol_description: str | None = Field(
        default=None, alias="symbolDescription"
    )
    beta: Decimal | None = None
    week_52_high: Decimal | None = Field(default=None, alias="week52High")
    week_52_low: Decimal | None = Field(default=None, alias="week52Low")
    market_cap: Decimal | None = Field(default=None, alias="marketCap")
    currency: str | None = None
    exchange: str | None = None


class Position(BaseModel):
    """Normalized position held in an E*TRADE account."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    position_id: int | None = Field(default=None, alias="positionId")
    symbol_description: str | None = Field(
        default=None, alias="symbolDescription"
    )
    date_acquired: int | None = Field(default=None, alias="dateAcquired")
    price_paid: Decimal | None = Field(default=None, alias="pricePaid")
    commissions: Decimal | None = None
    other_fees: Decimal | None = Field(default=None, alias="otherFees")
    quantity: Decimal | None = None
    position_indicator: str | None = Field(
        default=None, alias="positionIndicator"
    )
    position_type: str | None = Field(default=None, alias="positionType")
    days_gain: Decimal | None = Field(default=None, alias="daysGain")
    days_gain_pct: Decimal | None = Field(default=None, alias="daysGainPct")
    market_value: Decimal | None = Field(default=None, alias="marketValue")
    total_cost: Decimal | None = Field(default=None, alias="totalCost")
    total_gain: Decimal | None = Field(default=None, alias="totalGain")
    total_gain_pct: Decimal | None = Field(default=None, alias="totalGainPct")
    portfolio_pct: Decimal | None = Field(default=None, alias="pctOfPortfolio")
    cost_per_share: Decimal | None = Field(default=None, alias="costPerShare")
    today_commissions: Decimal | None = Field(
        default=None, alias="todayCommissions"
    )
    today_fees: Decimal | None = Field(default=None, alias="todayFees")
    today_price_paid: Decimal | None = Field(
        default=None, alias="todayPricePaid"
    )
    today_quantity: Decimal | None = Field(default=None, alias="todayQuantity")
    adjusted_previous_close: Decimal | None = Field(
        default=None, alias="adjPrevClose"
    )
    lots_details: str | None = Field(default=None, alias="lotsDetails")
    quote_details_url: str | None = Field(default=None, alias="quoteDetails")
    product: Product | None = Field(default=None, alias="Product")
    quote: QuoteDetails | None = Field(default=None, alias="Complete")

    @property
    def symbol(self) -> str | None:
        return self.product.symbol if self.product else None

    @property
    def current_price(self) -> Decimal | None:
        return self.quote.price if self.quote else None


class PortfolioTotals(BaseModel):
    """Account-level totals returned by E*TRADE."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    todays_gain_loss: Decimal | None = Field(
        default=None, alias="todaysGainLoss"
    )
    todays_gain_loss_pct: Decimal | None = Field(
        default=None, alias="todaysGainLossPct"
    )
    total_market_value: Decimal | None = Field(
        default=None, alias="totalMarketValue"
    )
    total_gain_loss: Decimal | None = Field(default=None, alias="totalGainLoss")
    total_gain_loss_pct: Decimal | None = Field(
        default=None, alias="totalGainLossPct"
    )
    total_price_paid: Decimal | None = Field(
        default=None, alias="totalPricePaid"
    )
    cash_balance: Decimal | None = Field(default=None, alias="cashBalance")


class PortfolioSnapshot(BaseModel):
    """Normalized portfolio snapshot consumed by analytics and reporting."""

    model_config = ConfigDict(extra="ignore")

    account_id: str | None = None
    account_id_key: str
    totals: PortfolioTotals
    positions: list[Position] = Field(default_factory=list)
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    source: str = "etrade"

    @classmethod
    def from_etrade_payload(
        cls,
        payload: dict[str, Any],
        account_id_key: str,
        *,
        retrieved_at: datetime | None = None,
    ) -> PortfolioSnapshot:
        response = payload.get("PortfolioResponse", {})
        account_portfolios = response.get("AccountPortfolio", [])
        if isinstance(account_portfolios, dict):
            account_portfolios = [account_portfolios]

        selected_account = next(
            (
                account
                for account in account_portfolios
                if account.get("accountId") == account_id_key
                or account.get("accountIdKey") == account_id_key
            ),
            None,
        )
        selected_account = selected_account or (
            account_portfolios[0] if account_portfolios else {}
        )

        positions = selected_account.get("Position", [])
        if isinstance(positions, dict):
            positions = [positions]

        return cls(
            account_id=selected_account.get("accountId"),
            account_id_key=account_id_key,
            totals=PortfolioTotals.model_validate(response.get("Totals", {})),
            positions=[Position.model_validate(position) for position in positions],
            retrieved_at=retrieved_at or datetime.now(timezone.utc),
        )
