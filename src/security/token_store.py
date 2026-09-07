"""Secure storage for E*TRADE OAuth tokens.

Uses ``keyring`` with the operating system's secure credential store. When
running under WSL, this is a Linux keyring environment, not Windows
Credential Manager. No plaintext fallback is allowed.
"""
from __future__ import annotations

import json

import keyring
import keyring.errors

from ..api.etrade_client import ETradeCredentials
from ..config import settings

_SERVICE_NAME = "tradebot-etrade"
_USERNAME = "oauth-tokens"  # single-user tool -> one stored credential set


class TokenStoreUnavailable(RuntimeError):
    """Raised when no secure OS credential backend is available."""


def _keyring_error() -> TokenStoreUnavailable:
    return TokenStoreUnavailable(
        "No secure keyring backend is available. "
        "For Windows Credential Manager, run this project with Windows Python "
        "and a Windows virtual environment (for example, `py -3.13 -m venv "
        ".venv-windows`). Do not install keyrings.alt or use a plaintext token "
        "file as a fallback."
    )


def save_tokens(access_token: str, access_token_secret: str) -> None:
    """Persist the access token pair to the OS secret store."""
    payload = json.dumps(
        {
            "access_token": access_token,
            "access_token_secret": access_token_secret,
        }
    )
    try:
        keyring.set_password(_SERVICE_NAME, _USERNAME, payload)
    except keyring.errors.NoKeyringError as error:
        raise _keyring_error() from error


def load_tokens() -> tuple[str, str] | None:
    """Return stored tokens, or ``None`` when no tokens have been saved."""
    try:
        raw = keyring.get_password(_SERVICE_NAME, _USERNAME)
    except keyring.errors.NoKeyringError as error:
        raise _keyring_error() from error
    if raw is None:
        return None
    data = json.loads(raw)
    return data["access_token"], data["access_token_secret"]


def clear_tokens() -> None:
    """Delete stored tokens, forcing re-authorization on next run."""
    try:
        keyring.delete_password(_SERVICE_NAME, _USERNAME)
    except keyring.errors.PasswordDeleteError:
        pass  # Already gone.
    except keyring.errors.NoKeyringError as error:
        raise _keyring_error() from error


def load_credentials() -> ETradeCredentials | None:
    """Build full credentials from config and the secure token store."""
    tokens = load_tokens()
    if tokens is None:
        return None

    access_token, access_token_secret = tokens
    return ETradeCredentials(
        consumer_key=settings.PROD_API_KEY,
        consumer_secret=settings.PROD_SECRET,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )