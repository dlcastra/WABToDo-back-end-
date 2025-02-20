from random import SystemRandom
from urllib.parse import urlencode

import requests
from autobahn.wamp import ApplicationError
from django.conf import settings
from django.urls import reverse_lazy
from oauthlib.common import UNICODE_ASCII_CHARACTER_SET

from core.google_credentials import google_raw_login_get_credentials
from users.user_credentials import GoogleAccessTokens


class GoogleRawLoginFlowService:
    """
    Service class for managing Google OAuth 2.0 login flow.

    This class provides methods to handle the various stages of the Google OAuth 2.0
    login flow, including generating authorization URLs, acquiring access and ID
    tokens, and retrieving user information from Google. It requires configuration
    and credentials to communicate with the Google OAuth 2.0 endpoints.

    Attributes:
        API_URI: Lazy-resolved URL for the API callback endpoint.
        GOOGLE_AUTH_URL: URL to request an OAuth authorization code from Google.
        GOOGLE_ACCESS_TOKEN_OBTAIN_URL: URL to exchange the authorization code
            for access and ID tokens.
        GOOGLE_USER_INFO_URL: URL to fetch user information from Google using the
            access token.
        SCOPES: List of scopes defining the level of access being requested
            during the Google authentication process.

    Methods:
        __init__: Initializes the service and loads Google client credentials.
        _generate_state_session_token: Generates a secure random state token
            used in the authorization process to prevent CSRF attacks.
        _get_redirect_uri: Constructs the redirect URI required for the OAuth
            flow, combining the domain and API callback endpoint.
        get_authorization_url: Assembles the complete Google authorization URL
            with required query parameters and generates a state token.
        get_user_info: Retrieves user information from Google using the access
            token provided by the application.
        get_tokens: Exchanges the OAuth authorization code for access and ID
            tokens to facilitate communication with Google APIs.

    """
    API_URI = reverse_lazy("api:users:callback-raw")
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_ACCESS_TOKEN_OBTAIN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    SCOPES = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]

    def __init__(self):
        self._credentials = google_raw_login_get_credentials()

    @staticmethod
    def _generate_state_session_token(length=30, chars=UNICODE_ASCII_CHARACTER_SET):
        # This is how it's implemented in the official SDK
        rand = SystemRandom()
        state = "".join(rand.choice(chars) for _ in range(length))
        return state

    def _get_redirect_uri(self):
        domain = f"http://{settings.ALLOWED_HOSTS[1]}:8000"
        api_uri = self.API_URI
        redirect_uri = f"{domain}{api_uri}"
        return redirect_uri

    def get_authorization_url(self):
        redirect_uri = self._get_redirect_uri()
        print(redirect_uri)
        state = self._generate_state_session_token()
        print("s", state)
        params = {
            "response_type": "code",
            "client_id": self._credentials.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.SCOPES),
            "state": state,
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "select_account",
        }
        print("p", params)
        query_params = urlencode(params)
        print("qp", query_params)
        authorization_url = f"{self.GOOGLE_AUTH_URL}?{query_params}"
        print(f"Authorization URL: {authorization_url}, State: {state}")
        return authorization_url, state

    def get_user_info(self, *, google_tokens: GoogleAccessTokens):
        access_token = google_tokens.access_token

        response = requests.get(self.GOOGLE_USER_INFO_URL, params={"access_token": access_token})

        if not response.ok:
            raise ApplicationError("Failed to obtain user info from Google.")

        return response.json()

    def get_tokens(self, *, code: str) -> GoogleAccessTokens:
        redirect_uri = self._get_redirect_uri()

        data = {
            "code": code,
            "client_id": self._credentials.client_id,
            "client_secret": self._credentials.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        response = requests.post(self.GOOGLE_ACCESS_TOKEN_OBTAIN_URL, data=data)

        if not response.ok:
            raise ApplicationError("Failed to obtain access token from Google.")

        tokens = response.json()
        google_tokens = GoogleAccessTokens(id_token=tokens["id_token"], access_token=tokens["access_token"])

        return google_tokens
