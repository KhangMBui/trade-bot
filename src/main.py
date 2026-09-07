from decimal import Decimal
import argparse

from .api.account import list_accounts, select_account
from .api.etrade_client import ETradeClient
from .api.portfolio import view_portfolio
from .config import settings
from .etrade_authorize import get_credentials
from .services.portfolio_service import get_latest_portfolio, sync_portfolio
from .storage.repositories import PortfolioRepository


def run_read_only_portfolio_review() -> None:
	"""Fetch and display a sanitized read-only portfolio summary."""
	credentials = get_credentials()
	client = ETradeClient(credentials)
	accounts = list_accounts(client)
	selected_account = select_account(
		accounts,
		preferred_account_id_key=settings.ACCOUNT_ID_KEY,
	)
	snapshot = view_portfolio(client, selected_account.account_id_key)
	_print_snapshot(selected_account.display_name, selected_account.account_type, snapshot)


def run_sync_portfolio() -> None:
	"""Fetch the selected E*TRADE portfolio and save a database snapshot."""

  # Get ETrade credentials
	credentials = get_credentials()

  # Initialize ETradeClient with the retrieved credentials
	client = ETradeClient(credentials)

  # List out all current ETrade accounts
	accounts = list_accounts(client)

  # Select one account
	selected_account = select_account(
		accounts,
		preferred_account_id_key=settings.ACCOUNT_ID_KEY,
	)

  # Initialize the storage repository
	repository = PortfolioRepository(settings.DATABASE_PATH)

  # Save a database snapshot
	snapshot = sync_portfolio(client, repository, selected_account.account_id_key)

	print(f"Saved portfolio snapshot for {selected_account.display_name}.")
	print(f"Database: {settings.DATABASE_PATH}")
	print(f"Positions saved: {len(snapshot.positions)}")
	print(f"Total market value: {_format_money(snapshot.totals.total_market_value)}")


def run_latest_portfolio() -> None:
	"""Read the latest local snapshot without contacting E*TRADE."""

  # Initialize repository
	repository = PortfolioRepository(settings.DATABASE_PATH)

  # Get latest snapshot
	snapshot = get_latest_portfolio(
		repository,
		account_id_key=settings.ACCOUNT_ID_KEY,
	)
	if snapshot is None:
		print("No saved portfolio snapshot exists. Run sync-portfolio first.")
		return

	_print_snapshot(snapshot.account_id_key, None, snapshot)


def _print_snapshot(
	account_name: str,
	account_type: str | None,
	snapshot,
) -> None:
	"""Print out portfolio snapshot details"""
	totals = snapshot.totals

	print(f"Account: {account_name}")
	print(f"Account type: {account_type or 'unknown'}")
	print(f"Total market value: {_format_money(totals.total_market_value)}")
	print(f"Cash balance: {_format_money(totals.cash_balance)}")
	print(f"Total gain/loss: {_format_money(totals.total_gain_loss)}")
	print("Positions:")
	for position in snapshot.positions:
		print(
			f"- {position.symbol or 'Unknown'}: "
			f"quantity={position.quantity}, "
			f"market_value={_format_money(position.market_value)}"
		)


def _format_money(value: Decimal | None) -> str:
	return "unavailable" if value is None else f"${value:,.2f}"


def main() -> None:
	parser = argparse.ArgumentParser(description="Read-only portfolio tools")
	parser.add_argument(
		"command",
		nargs="?",
		choices=("review", "sync-portfolio", "latest-portfolio"),
		default="review",
	)
	args = parser.parse_args()

	if args.command == "sync-portfolio":
		run_sync_portfolio()
	elif args.command == "latest-portfolio":
		run_latest_portfolio()
	else:
		run_read_only_portfolio_review()


if __name__ == "__main__":
	main()



