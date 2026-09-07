from requests_oauthlib import OAuth1Session

from .api.etrade_client import ETradeClient, ETradeCredentials
from .config import settings

# Production URLs
REQUEST_TOKEN_URL = "https://api.etrade.com/oauth/request_token"
AUTHORIZE_URL = "https://us.etrade.com/e/t/etws/authorize"
ACCESS_TOKEN_URL = "https://api.etrade.com/oauth/access_token"


def authorize() -> ETradeCredentials:
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

    return ETradeCredentials(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_tokens["oauth_token"],
        access_token_secret=access_tokens["oauth_token_secret"],
    )


def main() -> None:
    credentials = authorize()
    client = ETradeClient(credentials)
    accounts = client.list_accounts()
    portfolio = client.get_portfolio(settings.ACCOUNT_ID_KEY)

    print(f"Accounts response: {accounts}")
    print(f"Portfolio response: {portfolio}")


if __name__ == "__main__":
    main()
