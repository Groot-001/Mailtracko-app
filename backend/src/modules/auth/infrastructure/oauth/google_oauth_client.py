from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from httpx import AsyncClient

from src.core.config.settings import config
from src.shared.exceptions.base_exceptions import InvalidError, ServerError


@dataclass
class GoogleUserInfo:
    id: str
    email: str
    verified_email: bool
    name: str
    picture: str | None = None


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

SCOPES = [
    "openid",
    "email",
    "profile",
]


class GoogleOAuthClient:
    def __init__(self, client: AsyncClient | None = None):
        self._client = client or AsyncClient()

    def get_authorization_url(self, state: str) -> str:
        if not config.GOOGLE_CLIENT_ID:
            raise InvalidError(error="Google sign-in is not configured")
        params = {
            "client_id": config.GOOGLE_CLIENT_ID,
            "redirect_uri": config.google_redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
            raise InvalidError(error="Google sign-in is not configured")

        data = {
            "code": code,
            "client_id": config.GOOGLE_CLIENT_ID,
            "client_secret": config.GOOGLE_CLIENT_SECRET,
            "redirect_uri": config.google_redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            resp = await self._client.post(GOOGLE_TOKEN_URL, data=data)
        except Exception as exc:
            raise ServerError(
                error="Google sign-in could not reach Google. Please try again.",
                internal_details=str(exc),
            ) from exc

        if resp.is_error:
            try:
                body = resp.json()
            except Exception:
                body = {}

            google_error = str(body.get("error") or "").lower()
            description = str(body.get("error_description") or "").lower()

            if google_error == "invalid_grant":
                raise InvalidError(
                    error="Google sign-in expired or was already used. Please try signing in again."
                )
            if google_error in {"invalid_client", "unauthorized_client"}:
                raise InvalidError(
                    error="Google sign-in is not configured correctly. Please contact support."
                )
            if "redirect_uri" in description:
                raise InvalidError(
                    error="Google sign-in redirect configuration is invalid. Please contact support."
                )

            raise InvalidError(error="Google sign-in failed. Please try again.")

        tokens = resp.json()
        if not tokens.get("access_token"):
            raise InvalidError(error="Google did not return an access token. Please try again.")
        return tokens

    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            resp = await self._client.get(GOOGLE_USERINFO_URL, headers=headers)
        except Exception as exc:
            raise ServerError(
                error="Google profile could not be loaded. Please try again.",
                internal_details=str(exc),
            ) from exc

        if resp.status_code in {401, 403}:
            raise InvalidError(
                error="Google authorization is no longer valid. Please sign in with Google again."
            )
        if resp.is_error:
            raise InvalidError(error="Google profile could not be loaded. Please try again.")

        data = resp.json()
        if not data.get("id") or not data.get("email"):
            raise InvalidError(error="Google did not return the required account information.")

        return GoogleUserInfo(
            id=data["id"],
            email=data["email"],
            verified_email=data.get("verified_email", False),
            name=data.get("name", ""),
            picture=data.get("picture"),
        )
