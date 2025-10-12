from flask import current_app, url_for
from app.models import User, db

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build

    GOOGLE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Google OAuth modules not available: {e}")
    GOOGLE_MODULES_AVAILABLE = False
    Request = None
    Credentials = None
    Flow = None
    build = None


class GoogleOAuthService:
    SCOPES = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]

    def __init__(self):
        if not GOOGLE_MODULES_AVAILABLE:
            raise ImportError(
                "Google OAuth modules are not available. Please install google-auth, google-auth-oauthlib, and google-api-python-client"
            )

        self.client_id = current_app.config.get("GOOGLE_CLIENT_ID")
        self.client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = current_app.config.get("GOOGLE_REDIRECT_URI")

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Google OAuth credentials not configured properly")

    def get_authorization_url(self):
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=self.SCOPES,
        )
        flow.redirect_uri = self.redirect_uri

        authorization_url, state = flow.authorization_url(
            access_type="offline", include_granted_scopes="true"
        )

        return authorization_url, state

    def exchange_code_for_token(self, authorization_code, state=None):
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=self.SCOPES,
        )
        flow.redirect_uri = self.redirect_uri

        flow.fetch_token(code=authorization_code)

        return flow.credentials

    def get_user_info(self, credentials):
        service = build("oauth2", "v2", credentials=credentials)

        user_info = service.userinfo().get().execute()

        return {
            "id": user_info.get("id"),
            "email": user_info.get("email"),
            "given_name": user_info.get("given_name"),
            "family_name": user_info.get("family_name"),
            "picture": user_info.get("picture"),
            "verified_email": user_info.get("verified_email", False),
        }

    def revoke_credentials(self, credentials):
        try:
            credentials.revoke(Request())
        except Exception as e:
            current_app.logger.error(f"Error revoking credentials: {e}")

    @staticmethod
    def is_configured():
        if not GOOGLE_MODULES_AVAILABLE:
            return False
        return all(
            [
                current_app.config.get("GOOGLE_CLIENT_ID"),
                current_app.config.get("GOOGLE_CLIENT_SECRET"),
                current_app.config.get("GOOGLE_REDIRECT_URI"),
            ]
        )
