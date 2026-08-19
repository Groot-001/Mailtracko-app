from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlencode, urlparse
import re

from httpx import AsyncClient, Response

from src.core.config.settings import config
from src.shared.exceptions.base_exceptions import InvalidError


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"

# MailTracko imports from a Sheet URL supplied by the user. Drive-wide access is
# intentionally not requested: spreadsheets.readonly is sufficient for reading
# a spreadsheet the connected Google account can access and keeps OAuth consent
# to the minimum privilege required by this product flow.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
_SHEET_PATH_RE = re.compile(r"^/spreadsheets/d/([A-Za-z0-9_-]+)(?:/|$)")


@dataclass
class SheetInfo:
    spreadsheet_id: str
    title: str


class GoogleSheetsOAuthClient:
    def __init__(self, client: AsyncClient | None = None):
        self._client = client or AsyncClient()

    @property
    def client_id(self) -> str:
        return config.GOOGLE_SHEETS_CLIENT_ID or config.GOOGLE_CLIENT_ID

    @property
    def client_secret(self) -> str:
        return config.GOOGLE_SHEETS_CLIENT_SECRET or config.GOOGLE_CLIENT_SECRET

    @property
    def redirect_uri(self) -> str:
        return (config.GOOGLE_SHEETS_REDIRECT_URI or "").strip()

    @staticmethod
    def _response_payload(response: Response) -> dict[str, Any]:
        try:
            payload = response.json()
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    @classmethod
    def _token_error(cls, response: Response) -> InvalidError:
        payload = cls._response_payload(response)
        code = str(payload.get("error", "")).strip()
        description = str(payload.get("error_description", "")).strip()
        if code == "invalid_grant":
            return InvalidError(
                error="Your Google connection has expired or was revoked. Please reconnect your Google account."
            )
        if code in {"invalid_client", "unauthorized_client"}:
            return InvalidError(
                error="Google Sheets OAuth configuration is invalid. Please contact your workspace administrator."
            )
        if code == "redirect_uri_mismatch":
            return InvalidError(
                error="Google Sheets callback configuration does not match this environment. Please contact your workspace administrator."
            )
        return InvalidError(
            error=description or "Google authorization could not be completed. Please try again."
        )

    @classmethod
    def _sheets_api_error(cls, response: Response, *, data_request: bool = False) -> InvalidError:
        payload = cls._response_payload(response)
        error_payload = payload.get("error") if isinstance(payload.get("error"), dict) else {}
        message = str(error_payload.get("message", "")).strip()
        status = str(error_payload.get("status", "")).strip().upper()
        details = error_payload.get("details") if isinstance(error_payload.get("details"), list) else []
        detail_text = " ".join(str(detail) for detail in details)
        combined = f"{message} {status} {detail_text}".lower()

        if response.status_code == 401:
            return InvalidError(
                error="Your Google Sheets connection is no longer valid. Reconnect your Google account and try again."
            )

        if response.status_code == 403:
            if any(
                marker in combined
                for marker in (
                    "accessnotconfigured",
                    "service_disabled",
                    "api has not been used",
                    "sheets.googleapis.com has not been used",
                    "google sheets api has not been used",
                )
            ):
                return InvalidError(
                    error="Google Sheets API is not enabled for this Google Cloud project. Enable the Google Sheets API, then reconnect Google and try again."
                )
            if any(
                marker in combined
                for marker in (
                    "insufficient authentication scopes",
                    "access_token_scope_insufficient",
                    "insufficientpermissions",
                    "insufficient permission",
                )
            ):
                return InvalidError(
                    error="MailTracko was not granted read access to Google Sheets. Reconnect your Google account and approve spreadsheet read permission."
                )
            return InvalidError(
                error="The connected Google account cannot read this spreadsheet. Open the sheet with the same Google account or update its sharing permission, then try again."
            )

        if response.status_code == 404:
            return InvalidError(
                error=(
                    "Google Sheet or selected worksheet was not found. Check the spreadsheet URL and worksheet name."
                    if data_request
                    else "Google Sheet was not found. Check the spreadsheet URL and make sure it has not been deleted."
                )
            )

        if response.status_code == 400:
            return InvalidError(
                error=(
                    "The selected Google Sheet worksheet or range is invalid. Reload worksheets and try again."
                    if data_request
                    else "Google rejected this spreadsheet request. Check the Google Sheets URL and try again."
                )
            )

        return InvalidError(
            error=message or "Google Sheets could not complete the request. Please try again."
        )

    def _validate_oauth_configuration(self, *, require_secret: bool = False) -> None:
        if not self.client_id or not self.redirect_uri or (require_secret and not self.client_secret):
            raise InvalidError(
                error="Google Sheets OAuth is not configured for this environment. Please contact your workspace administrator."
            )

    def get_authorization_url(self, state: str) -> str:
        self._validate_oauth_configuration()
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "state": state,
            "access_type": "offline",
            # Consent is intentional here: MailTracko needs a refresh token for
            # later imports, not a one-session access token.
            "prompt": "consent",
            "include_granted_scopes": "true",
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        self._validate_oauth_configuration(require_secret=True)
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        resp = await self._client.post(GOOGLE_TOKEN_URL, data=data)
        if resp.is_error:
            raise self._token_error(resp)
        payload = resp.json()
        if not payload.get("access_token"):
            raise InvalidError(error="Google did not return an access token. Please reconnect and try again.")
        return payload

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        self._validate_oauth_configuration(require_secret=True)
        if not refresh_token:
            raise InvalidError(error="Google Sheets is not connected. Please reconnect your Google account.")
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        resp = await self._client.post(GOOGLE_TOKEN_URL, data=data)
        if resp.is_error:
            raise self._token_error(resp)
        payload = resp.json()
        if not payload.get("access_token"):
            raise InvalidError(error="Google did not return an access token. Please reconnect and try again.")
        return payload

    async def get_sheet_metadata(self, access_token: str, spreadsheet_id: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        # Request only the fields needed for worksheet selection. This is faster
        # and avoids pulling the entire spreadsheet metadata payload.
        resp = await self._client.get(
            f"{GOOGLE_SHEETS_API}/{spreadsheet_id}",
            headers=headers,
            params={"fields": "spreadsheetId,properties.title,sheets.properties"},
        )
        if resp.is_error:
            raise self._sheets_api_error(resp)
        return resp.json()

    async def get_sheet_data(
        self,
        access_token: str,
        spreadsheet_id: str,
        range_: str,
    ) -> list[list[str]]:
        headers = {"Authorization": f"Bearer {access_token}"}
        encoded_range = quote(range_, safe="")
        resp = await self._client.get(
            f"{GOOGLE_SHEETS_API}/{spreadsheet_id}/values/{encoded_range}",
            headers=headers,
        )
        if resp.is_error:
            raise self._sheets_api_error(resp, data_request=True)
        data = resp.json()
        return data.get("values", [])

    def extract_sheet_id_from_url(self, url: str) -> str:
        value = (url or "").strip()
        if not value:
            raise InvalidError(error="Google Sheets URL is required.")
        try:
            parsed = urlparse(value)
        except ValueError as exc:
            raise InvalidError(error="Invalid Google Sheets URL. Paste the full spreadsheet URL.") from exc

        if parsed.scheme != "https" or parsed.hostname != "docs.google.com":
            raise InvalidError(
                error="Invalid Google Sheets URL. Paste a full https://docs.google.com/spreadsheets URL."
            )
        match = _SHEET_PATH_RE.match(parsed.path)
        if not match:
            raise InvalidError(
                error="Invalid Google Sheets URL. Paste a full https://docs.google.com/spreadsheets/d/... URL."
            )
        return match.group(1)
