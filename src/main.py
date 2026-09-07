from decimal import Decimal
import argparse
from collections.abc import Callable
from typing import TypeVar

from requests.exceptions import HTTPError

from .api.account import list_accounts, select_account
from .api.etrade_client import ETradeClient
from .api.portfolio import view_portfolio
from .config import settings
from .etrade_authorize import (
	get_credentials,
	recover_from_rejected_token,
)
from .security import token_store
from .services.portfolio_service import (
	get_latest_portfolio, 
	sync_portfolio,
  analyze_latest_portfolio
)
from .storage.repositories import PortfolioRepository


T = TypeVar("T")


def run_read_only_portfolio_review() -> None:
	"""Fetch and display a sanitized read-only portfolio summary."""
	selected_account, snapshot = _with_token_recovery(_review_from_client)
	_print_snapshot(selected_account.display_name, selected_account.account_type, snapshot)


def run_sync_portfolio() -> None:
	"""Fetch the selected E*TRADE portfolio and save a database snapshot."""
	selected_account, snapshot = _with_token_recovery(_sync_from_client)

  # Initialize the storage repository
	repository = PortfolioRepository(settings.DATABASE_PATH)

  # Save a database snapshot
	repository.save_snapshot(snapshot)

	print(f"Saved portfolio snapshot for {selected_account.display_name}.")
	print(f"Database: {settings.DATABASE_PATH}")
	print(f"Positions saved: {len(snapshot.positions)}")
	print(f"Total market value: {_format_money(snapshot.totals.total_market_value)}")


def run_reauthorize() -> None:
	"""Clear the cached token and run the interactive OAuth flow."""
	token_store.clear_tokens()
	get_credentials()
	print("Authorization completed and the new token was saved securely.")


def _review_from_client(client: ETradeClient):
	accounts = list_accounts(client)
	selected_account = select_account(
		accounts,
		preferred_account_id_key=settings.ACCOUNT_ID_KEY,
	)
	snapshot = view_portfolio(client, selected_account.account_id_key)
	return selected_account, snapshot


def _sync_from_client(client: ETradeClient):
	accounts = list_accounts(client)
	selected_account = select_account(
		accounts,
		preferred_account_id_key=settings.ACCOUNT_ID_KEY,
	)
	snapshot = view_portfolio(client, selected_account.account_id_key)
	return selected_account, snapshot


def _with_token_recovery(operation: Callable[[ETradeClient], T]) -> T:
	"""Run one read-only operation and recover once from a rejected token."""
	client = ETradeClient(get_credentials())
	try:
		return operation(client)
	except HTTPError as error:
		if error.response is None or error.response.status_code != 401:
			raise

		print("E*TRADE rejected the cached token. Attempting token recovery...")
		recovered_client = ETradeClient(recover_from_rejected_token())
		return operation(recovered_client)


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

def _format_percent(value: Decimal | None) -> str:
    return "unavailable" if value is None else f"{value:.2%}"

def run_analyze_portfolio() -> None:
  """Analyze the latest saved snapshot without contacting E*TRADE."""
  repository = PortfolioRepository(settings.DATABASE_PATH)

  analysis = analyze_latest_portfolio(
    repository,
    account_id_key=settings.ACCOUNT_ID_KEY,
  )

  if analysis is None:
    print("No saved portfolio snapshot exists.")
    print("Run sync-portfolio first.")
    return

  print(f"Account key: {analysis.account_id_key}")
  print(f"Analyzed at: {analysis.analyzed_at}")
  print(f"Positions: {analysis.position_count}")
  print(
    f"Total market value: "
    f"{_format_money(analysis.total_market_value)}"
  )
  print(f"Cash balance: {_format_money(analysis.cash_balance)}")
  print(f"Cash weight: {_format_percent(analysis.cash_weight)}")
  print(f"Total gain/loss: {_format_money(analysis.total_gain_loss)}")
  print(
    f"Total gain/loss percentage: "
    f"{_format_percent(analysis.total_gain_loss_pct)}"
  )

  if analysis.largest_position is not None:
    largest = analysis.largest_position
    print(
        f"Largest position: {largest.symbol} "
        f"({_format_percent(largest.portfolio_weight)})"
    )

  print()
  print("Positions:")

  for position in analysis.positions:
    print(
      f"- {position.symbol}: "
      f"weight={_format_percent(position.portfolio_weight)}, "
      f"value={_format_money(position.market_value)}, "
      f"gain/loss={_format_money(position.total_gain)}"
    )

    for flag in position.risk_flags:
      print(f"  warning: {flag}")

  print()

  if analysis.risk_flags:
    print("Portfolio risk flags:")
    for flag in analysis.risk_flags:
      print(f"- {flag}")
  else:
    print("Portfolio risk flags: none")



def main() -> None:
	parser = argparse.ArgumentParser(description="Read-only portfolio tools")
	parser.add_argument(
		"command",
		nargs="?",
    choices=(
        "review",
        "sync-portfolio",
        "latest-portfolio",
        "analyze-portfolio",
		"reauthorize",
    ),
		default="review",
	)
	args = parser.parse_args()

	if args.command == "sync-portfolio":
		run_sync_portfolio()
	elif args.command == "latest-portfolio":
		run_latest_portfolio()
	elif args.command == "analyze-portfolio":
		run_analyze_portfolio()
	elif args.command == "reauthorize":
		run_reauthorize()
	else:
		run_read_only_portfolio_review()


if __name__ == "__main__":
	main()



