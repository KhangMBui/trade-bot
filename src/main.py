from decimal import Decimal

from .api.account import list_accounts, select_account
from .api.etrade_client import ETradeClient
from .api.portfolio import view_portfolio
from .config import settings
from .etrade_authorize import get_credentials


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
	totals = snapshot.totals

	print(f"Account: {selected_account.display_name}")
	print(f"Account type: {selected_account.account_type or 'unknown'}")
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


if __name__ == "__main__":
	run_read_only_portfolio_review()



