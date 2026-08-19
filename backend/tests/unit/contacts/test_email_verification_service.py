from types import SimpleNamespace

import pytest

from src.modules.contacts.application import verification
from src.modules.contacts.application.verification import EmailVerificationService
from src.shared.exceptions.base_exceptions import InvalidError


class _ProviderResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "status": "risky",
            "reason": "accept_all",
            "score": 60,
            "domain": {
                "name": "example.com",
                "acceptAll": "yes",
                "disposable": "no",
                "free": "no",
            },
            "account": {"role": "no", "disabled": "no", "fullMailbox": "no"},
            "dns": {"record": "mx.example.com", "type": "MX"},
        }


class _ProviderClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def get(self, *_args, **_kwargs):
        return _ProviderResponse()


@pytest.mark.asyncio
async def test_verification_requires_provider_configuration(monkeypatch) -> None:
    monkeypatch.setattr(verification, "config", SimpleNamespace(BOUNCER_API_KEY="", BOUNCER_API_BASE_URL="https://api.usebouncer.com/v1.1"))

    with pytest.raises(InvalidError, match="not available"):
        await EmailVerificationService().verify("recipient@example.com")


@pytest.mark.asyncio
async def test_verification_maps_live_provider_result(monkeypatch) -> None:
    monkeypatch.setattr(
        verification,
        "config",
        SimpleNamespace(BOUNCER_API_KEY="provider-test-key", BOUNCER_API_BASE_URL="https://api.usebouncer.com/v1.1"),
    )
    monkeypatch.setattr(
        verification.httpx,
        "AsyncClient",
        lambda **_kwargs: _ProviderClient(),
    )

    result = await EmailVerificationService().verify("recipient@example.com")

    assert result["status"] == "catch-all"
    assert result["score"] == 60
    assert result["bounce_risk"] == "medium"
    assert result["details"]["mx_found"] is True

class _AuthRejectedResponse:
    status_code = 401

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {}


class _AuthRejectedClient(_ProviderClient):
    async def get(self, *_args, **_kwargs):
        return _AuthRejectedResponse()


@pytest.mark.asyncio
async def test_verification_reports_rejected_provider_credentials(monkeypatch) -> None:
    monkeypatch.setattr(
        verification,
        "config",
        SimpleNamespace(BOUNCER_API_KEY="rejected-key", BOUNCER_API_BASE_URL="https://api.usebouncer.com/v1.1"),
    )
    monkeypatch.setattr(
        verification.httpx,
        "AsyncClient",
        lambda **_kwargs: _AuthRejectedClient(),
    )

    with pytest.raises(InvalidError, match="rejected the credentials"):
        await EmailVerificationService().verify("recipient@example.com")
