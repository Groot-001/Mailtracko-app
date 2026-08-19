import json
import sys
import types
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

# The production dependency is declared by the project but is not installed in this
# sandbox. Stub only the import surface needed to load redis_client for this unit test.
_stubbed_redis = "redis.asyncio" not in sys.modules
if _stubbed_redis:
    redis_module = types.ModuleType("redis")
    redis_asyncio_module = types.ModuleType("redis.asyncio")
    redis_asyncio_module.ConnectionPool = object
    redis_asyncio_module.Redis = object
    redis_module.asyncio = redis_asyncio_module
    sys.modules["redis"] = redis_module
    sys.modules["redis.asyncio"] = redis_asyncio_module

from src.modules.email_account.application.usecases.oauth_callback_usecase import OAuthCallbackUseCase

if _stubbed_redis:
    sys.modules.pop("redis.asyncio", None)
    sys.modules.pop("redis", None)
from src.modules.email_account.domain.entities.email_account_entity import EmailAccountEntity
from src.modules.email_account.domain.entities.oauth_config_entity import OauthConfigEntity


@pytest.mark.asyncio
async def test_oauth_callback_restores_soft_deleted_account_instead_of_inserting_duplicate(monkeypatch) -> None:
    redis = MagicMock()
    redis.get = AsyncMock(
        return_value=json.dumps(
            {
                "provider": "gmail",
                "organization_id": 9,
                "actor_id": 7,
                "email": None,
            }
        )
    )
    redis.delete = AsyncMock()
    monkeypatch.setattr(
        "src.modules.email_account.application.usecases.oauth_callback_usecase.get_redis",
        AsyncMock(return_value=redis),
    )
    monkeypatch.setattr(
        "src.modules.email_account.application.usecases.oauth_callback_usecase.encrypt",
        lambda value: f"encrypted:{value}",
    )
    publish = AsyncMock()
    monkeypatch.setattr(
        "src.modules.email_account.application.usecases.oauth_callback_usecase.mediator.publish",
        publish,
    )

    account = EmailAccountEntity(
        id=42,
        uuid="account-uuid",
        organization_id=9,
        provider="gmail",
        email="sender@example.com",
        sender_name="Sender",
        status="disconnected",
        oauth_config_id=55,
        deleted_at=datetime.now(UTC),
    )

    service = MagicMock()
    service.get_by_email_and_organization = AsyncMock(return_value=None)
    service.get_by_email_and_organization_including_deleted = AsyncMock(return_value=account)
    service.create_oauth_config = AsyncMock(
        return_value=OauthConfigEntity(id=99, encrypted_refresh_token="encrypted:new-refresh")
    )
    service.update_account = AsyncMock(side_effect=lambda entity: entity)
    service.create_account = AsyncMock(side_effect=AssertionError("duplicate insert attempted"))
    service.get_oauth_config = AsyncMock(return_value=None)
    service.update_oauth_config = AsyncMock()

    oauth_client = MagicMock()
    oauth_client.exchange_code = AsyncMock(
        return_value={"access_token": "access", "refresh_token": "new-refresh"}
    )
    oauth_client.get_user_info = AsyncMock(
        return_value=SimpleNamespace(email="sender@example.com", name="Sender")
    )
    test_connection = MagicMock()
    test_connection.execute = AsyncMock(return_value={"healthy": True})

    result = await OAuthCallbackUseCase(
        email_account_domain_service=service,
        google_mail_oauth_client=oauth_client,
        test_connection_usecase=test_connection,
    ).execute(code="oauth-code", state="oauth-state")

    assert result["uuid"] == "account-uuid"
    assert result["status"] == "active"
    assert account.deleted_at is None
    assert account.oauth_config_id == 99
    service.create_account.assert_not_awaited()
    service.get_by_email_and_organization_including_deleted.assert_awaited_once_with(
        email="sender@example.com",
        organization_id=9,
    )
    service.update_account.assert_awaited_once_with(account)
    test_connection.execute.assert_awaited_once_with(
        account_uuid="account-uuid",
        organization_id=9,
        actor_id=7,
    )
