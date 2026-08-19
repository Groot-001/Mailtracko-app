from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from src.modules.contacts.infrastructure.oauth.google_sheets_oauth_client import (
    GoogleSheetsOAuthClient,
)
from src.shared.exceptions.base_exceptions import InvalidError


def _configured_client(monkeypatch, http_client=None):
    monkeypatch.setattr(GoogleSheetsOAuthClient, "client_id", property(lambda self: "client-id"))
    monkeypatch.setattr(GoogleSheetsOAuthClient, "client_secret", property(lambda self: "client-secret"))
    monkeypatch.setattr(
        GoogleSheetsOAuthClient,
        "redirect_uri",
        property(lambda self: "http://localhost:3000/api/v1/contact-lists/sheets/oauth/callback"),
    )
    return GoogleSheetsOAuthClient(http_client)


def test_google_sheets_authorization_uses_minimum_readonly_scope_and_exact_callback(monkeypatch):
    client = _configured_client(monkeypatch)
    url = client.get_authorization_url("state-value")
    query = parse_qs(urlparse(url).query)

    assert query["redirect_uri"] == [
        "http://localhost:3000/api/v1/contact-lists/sheets/oauth/callback"
    ]
    assert query["scope"] == ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]
    assert query["include_granted_scopes"] == ["true"]


def test_extract_sheet_id_accepts_google_sheet_and_rejects_non_sheet_urls():
    client = GoogleSheetsOAuthClient()
    assert (
        client.extract_sheet_id_from_url(
            "https://docs.google.com/spreadsheets/d/abc_DEF-123/edit#gid=0"
        )
        == "abc_DEF-123"
    )

    with pytest.raises(InvalidError, match="docs.google.com"):
        client.extract_sheet_id_from_url("https://example.com/not-a-sheet")


@pytest.mark.asyncio
async def test_sheet_metadata_403_api_disabled_returns_actionable_error(monkeypatch):
    async def handler(request: httpx.Request):
        return httpx.Response(
            403,
            request=request,
            json={
                "error": {
                    "status": "PERMISSION_DENIED",
                    "message": "Google Sheets API has not been used in project before or it is disabled",
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = _configured_client(monkeypatch, http_client)
        with pytest.raises(InvalidError, match="Google Sheets API is not enabled"):
            await client.get_sheet_metadata("access-token", "sheet-id")


@pytest.mark.asyncio
async def test_sheet_metadata_401_requests_reconnect(monkeypatch):
    async def handler(request: httpx.Request):
        return httpx.Response(401, request=request, json={"error": {"message": "Invalid Credentials"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = _configured_client(monkeypatch, http_client)
        with pytest.raises(InvalidError, match="Reconnect your Google account"):
            await client.get_sheet_metadata("expired-token", "sheet-id")
