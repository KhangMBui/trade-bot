from requests_oauthlib import OAuth1Session

from .api.etrade_client import ETradeCredentials
from .config import settings
from .security import token_store

# Production URLs
REQUEST_TOKEN_URL = "https://api.etrade.com/oauth/request_token"
AUTHORIZE_URL = "https://us.etrade.com/e/t/etws/authorize"
ACCESS_TOKEN_URL = "https://api.etrade.com/oauth/access_token"
ACCESS_TOKEN_RENEW_URL = "https://api.etrade.com/oauth/renew_access_token"


def _interactive_authorize() -> ETradeCredentials:
    """Full OAuth1 dance with a browser + verifier code.
 
    Only runs when there's no usable stored token (first run, or the
    stored token has hard-expired past the E*TRADE midnight-ET cutoff).
    """
    consumer_key = settings.PROD_API_KEY
    consumer_secret = settings.PROD_SECRET
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        callback_uri="oob",
    )

    request_tokens = oauth.fetch_request_token(REQUEST_TOKEN_URL)
    request_token = request_tokens["oauth_token"]
    request_token_secret = request_tokens["oauth_token_secret"]

    print(
        f"Open this URL in your browser: {AUTHORIZE_URL}?key={consumer_key}&token={request_token}"
    )
    oauth_verifier = input("Paste oauth_verifier: ").strip()

    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=request_token,
        resource_owner_secret=request_token_secret,
        verifier=oauth_verifier,
    )
    access_tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)

    # Save the token into token store
    token_store.save_tokens(access_tokens["oauth_token"], access_tokens["oauth_token_secret"])

    return ETradeCredentials(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_tokens["oauth_token"],
        access_token_secret=access_tokens["oauth_token_secret"],
    )

def _try_renew(credentials: ETradeCredentials) -> bool:
    """Reactivate a token that went idle after 2 hours of no requests.
 
    Fails (returns False) once the token has crossed midnight US Eastern,
    at which point a full interactive re-authorization is required.
    """
    oauth = OAuth1Session(
        credentials.consumer_key,
        client_secret=credentials.consumer_secret,
        resource_owner_key=credentials.access_token,
        resource_owner_secret=credentials.access_token_secret,
    )
    response = oauth.get(ACCESS_TOKEN_RENEW_URL)
    return response.ok

def get_credentials() -> ETradeCredentials:
    """Entry point for a normal run: reuse a stored token if there is one."""
    cached = token_store.load_credentials()
    if cached is not None:
        return cached
    return _interactive_authorize()

def recover_from_rejected_token() -> ETradeCredentials:
    """Call this when a request to E*TRADE fails with 401 / invalid token.
 
    Tries the lightweight renew endpoint first (no browser needed), and
    only falls back to the full interactive flow if that fails.
    """
    cached = token_store.load_credentials()
    if cached is not None and _try_renew(cached):
        return cached  # token/secret pair is unchanged, just reactivated
 
    token_store.clear_tokens()
    return _interactive_authorize()