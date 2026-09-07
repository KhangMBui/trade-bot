from collections.abc import Callable

from .etrade_client import ETradeClient
from ..models.account import Account


def list_accounts(client: ETradeClient) -> list[Account]:
    """Return normalized accounts available to the authenticated user."""
    return client.list_account_models()


def select_account(
    accounts: list[Account],
    preferred_account_id_key: str | None = None,
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> Account:
    """Return a preferred account or prompt for a valid account selection."""
    if not accounts:
        raise ValueError("No E*TRADE accounts were returned.")

    if preferred_account_id_key:
        for account in accounts:
            if account.account_id_key == preferred_account_id_key:
                return account

    output_fn("Available E*TRADE accounts:")
    for index, account in enumerate(accounts, start=1):
        account_type = account.account_type or "unknown type"
        output_fn(f"{index}. {account.display_name} ({account_type})")

    while True:
        raw_selection = input_fn("Select an account number: ").strip()
        try:
            selection = int(raw_selection)
        except ValueError:
            output_fn("Please enter a whole number.")
            continue

        if 1 <= selection <= len(accounts):
            return accounts[selection - 1]

        output_fn(f"Choose a number from 1 to {len(accounts)}.")
