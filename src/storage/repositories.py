from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from ..models.portfolio import (
    PortfolioSnapshot,
    PortfolioTotals,
    Position,
    Product,
    QuoteDetails,
)
from .database import connection_scope, initialize_database


class PortfolioRepository:
    """SQLite persistence for normalized portfolio snapshots."""

    def __init__(self, database_path: str):
        self._database_path = database_path
        initialize_database(database_path)

    def save_snapshot(self, snapshot: PortfolioSnapshot) -> int:
        """Save a new portfolio snapshot into a records in the database"""
        with connection_scope(self._database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO portfolio_snapshots
                    (account_id, account_id_key, retrieved_at, source)
                VALUES (?, ?, ?, ?)
                """,
                (
                    snapshot.account_id,
                    snapshot.account_id_key,
                    snapshot.retrieved_at.isoformat(),
                    snapshot.source,
                ),
            )
            snapshot_id = int(cursor.lastrowid)
            totals = snapshot.totals
            connection.execute(
                """
                INSERT INTO portfolio_totals (
                    snapshot_id, todays_gain_loss, todays_gain_loss_pct,
                    total_market_value, total_gain_loss, total_gain_loss_pct,
                    total_price_paid, cash_balance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id,
                    _text(totals.todays_gain_loss),
                    _text(totals.todays_gain_loss_pct),
                    _text(totals.total_market_value),
                    _text(totals.total_gain_loss),
                    _text(totals.total_gain_loss_pct),
                    _text(totals.total_price_paid),
                    _text(totals.cash_balance),
                ),
            )
            for position in snapshot.positions:
                connection.execute(
                    """
                    INSERT INTO positions (
                        snapshot_id, position_id, symbol, symbol_description,
                        quantity, market_value, total_cost, total_gain,
                        total_gain_pct, portfolio_pct, current_price, currency,
                        product_json, quote_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot_id,
                        position.position_id,
                        position.symbol,
                        position.symbol_description,
                        _text(position.quantity),
                        _text(position.market_value),
                        _text(position.total_cost),
                        _text(position.total_gain),
                        _text(position.total_gain_pct),
                        _text(position.portfolio_pct),
                        _text(position.current_price),
                        position.quote.currency if position.quote else None,
                        _json(position.product),
                        _json(position.quote),
                    ),
                )
        return snapshot_id

    def get_latest_snapshot(
        self, account_id_key: str | None = None
    ) -> PortfolioSnapshot | None:
        """Retrieved the latest saved portfolio snapshot from the database"""
        with connection_scope(self._database_path) as connection:
            if account_id_key:
                snapshot_row = connection.execute(
                    """
                    SELECT * FROM portfolio_snapshots
                    WHERE account_id_key = ?
                    ORDER BY retrieved_at DESC, id DESC
                    LIMIT 1
                    """,
                    (account_id_key,),
                ).fetchone()
            else:
                snapshot_row = connection.execute(
                    """
                    SELECT * FROM portfolio_snapshots
                    ORDER BY retrieved_at DESC, id DESC
                    LIMIT 1
                    """
                ).fetchone()

            if snapshot_row is None:
                return None

            totals_row = connection.execute(
                "SELECT * FROM portfolio_totals WHERE snapshot_id = ?",
                (snapshot_row["id"],),
            ).fetchone()
            position_rows = connection.execute(
                "SELECT * FROM positions WHERE snapshot_id = ? ORDER BY id",
                (snapshot_row["id"],),
            ).fetchall()

        if totals_row is None:
            raise RuntimeError("Snapshot is missing its totals record.")

        return PortfolioSnapshot(
            account_id=snapshot_row["account_id"],
            account_id_key=snapshot_row["account_id_key"],
            retrieved_at=datetime.fromisoformat(snapshot_row["retrieved_at"]),
            source=snapshot_row["source"],
            totals=PortfolioTotals(
                todays_gain_loss=_decimal(totals_row["todays_gain_loss"]),
                todays_gain_loss_pct=_decimal(totals_row["todays_gain_loss_pct"]),
                total_market_value=_decimal(totals_row["total_market_value"]),
                total_gain_loss=_decimal(totals_row["total_gain_loss"]),
                total_gain_loss_pct=_decimal(totals_row["total_gain_loss_pct"]),
                total_price_paid=_decimal(totals_row["total_price_paid"]),
                cash_balance=_decimal(totals_row["cash_balance"]),
            ),
            positions=[_position_from_row(row) for row in position_rows],
        )

    def count_snapshots(self, account_id_key: str | None = None) -> int:
        with connection_scope(self._database_path) as connection:
            if account_id_key:
                row = connection.execute(
                    "SELECT COUNT(*) AS count FROM portfolio_snapshots WHERE account_id_key = ?",
                    (account_id_key,),
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT COUNT(*) AS count FROM portfolio_snapshots"
                ).fetchone()
        return int(row["count"])


def _text(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _decimal(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _json(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json", by_alias=True)
    return json.dumps(value)


def _position_from_row(row: Any) -> Position:
    product_data = json.loads(row["product_json"]) if row["product_json"] else None
    quote_data = json.loads(row["quote_json"]) if row["quote_json"] else None
    if quote_data and row["currency"] and "currency" not in quote_data:
        quote_data["currency"] = row["currency"]

    return Position(
        position_id=row["position_id"],
        symbol_description=row["symbol_description"],
        quantity=_decimal(row["quantity"]),
        market_value=_decimal(row["market_value"]),
        total_cost=_decimal(row["total_cost"]),
        total_gain=_decimal(row["total_gain"]),
        total_gain_pct=_decimal(row["total_gain_pct"]),
        portfolio_pct=_decimal(row["portfolio_pct"]),
        product=Product.model_validate(product_data) if product_data else None,
        quote=QuoteDetails.model_validate(quote_data) if quote_data else None,
    )
