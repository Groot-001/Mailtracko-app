from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from httpx import AsyncClient

from src.core.config.settings import config
from src.shared.exceptions.base_exceptions import InvalidError


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_GMAIL_SEND_URL = ("https://gmail.googleapis.com/gmail/v1/users/me/messages/send")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


@dataclass
class GoogleMailUserInfo:
    id: str
    email: str
    name: str
    picture: str | None = None


class GoogleMailOAuthClient:

    def __init__(self, client: AsyncClient | None = None):
        self._client = client or AsyncClient()

    @property
    def client_id(self) -> str:
        return config.GOOGLE_MAIL_CLIENT_ID or config.GOOGLE_CLIENT_ID

    @property
    def client_secret(self) -> str:
        return config.GOOGLE_MAIL_CLIENT_SECRET or config.GOOGLE_CLIENT_SECRET

    def get_authorization_url(self, state: str) -> str:
        if not self.client_id:
            raise InvalidError(error="Gmail sender OAuth is not configured")
        params = {
            "client_id": self.client_id,
            "redirect_uri": config.GOOGLE_MAIL_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        if not self.client_id or not self.client_secret:
            raise InvalidError(error="Gmail sender OAuth is not configured")
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": config.GOOGLE_MAIL_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        resp = await self._client.post(GOOGLE_TOKEN_URL, data=data)
        resp.raise_for_status()
        return resp.json()

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        if not self.client_id or not self.client_secret:
            raise InvalidError(error="Gmail sender OAuth is not configured")
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        resp = await self._client.post(GOOGLE_TOKEN_URL, data=data)
        resp.raise_for_status()
        return resp.json()

    async def get_user_info(self, access_token: str) -> GoogleMailUserInfo:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = await self._client.get(GOOGLE_USERINFO_URL, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return GoogleMailUserInfo(
            id=data["id"],
            email=data["email"],
            name=data.get("name", ""),
            picture=data.get("picture"),
        )
    async def send_raw_message(
        self,
        access_token: str,
        raw_message: str,
    ) -> dict[str, Any]:
        """
        Sends a MIME email through the Gmail API.
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        response = await self._client.post(
            GOOGLE_GMAIL_SEND_URL,
            headers=headers,
            json={
                "raw": raw_message,
            },
        )
        response.raise_for_status()

        return response.json()