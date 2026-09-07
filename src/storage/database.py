from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT,
    account_id_key TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    source TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolio_totals (
    snapshot_id INTEGER PRIMARY KEY,
    todays_gain_loss TEXT,
    todays_gain_loss_pct TEXT,
    total_market_value TEXT,
    total_gain_loss TEXT,
    total_gain_loss_pct TEXT,
    total_price_paid TEXT,
    cash_balance TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES portfolio_snapshots(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    position_id INTEGER,
    symbol TEXT,
    symbol_description TEXT,
    quantity TEXT,
    market_value TEXT,
    total_cost TEXT,
    total_gain TEXT,
    total_gain_pct TEXT,
    portfolio_pct TEXT,
    current_price TEXT,
    currency TEXT,
    product_json TEXT,
    quote_json TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES portfolio_snapshots(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_snapshots_account_time
    ON portfolio_snapshots(account_id_key, retrieved_at DESC);

CREATE INDEX IF NOT EXISTS idx_positions_snapshot
    ON positions(snapshot_id);
"""


def connect(database_path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection configured for this application."""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def connection_scope(database_path: str | Path) -> Iterator[sqlite3.Connection]:
    """Yield a connection and always close it after use."""
    connection = connect(database_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(database_path: str | Path) -> None:
    """Create the database schema if it does not already exist."""
    with connection_scope(database_path) as connection:
        connection.executescript(SCHEMA)
