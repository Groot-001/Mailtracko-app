import importlib.util
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

# Router-level tests require the full runtime dependency set installed by the
# project lock file/Docker image. The execution sandbox lacks these packages.
pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("redis") is None
    or importlib.util.find_spec("dependency_injector") is None,
    reason="full backend runtime dependencies are not installed",
)

from src.modules.auth.presentation.schemas.auth_schemas import RegisterRequest
from src.modules.email_template.presentation.schemas.template_schemas import (
    TemplateDetailResponseSchema,
)
from src.modules.organization.presentation.schemas.organization_schemas import (
    DeclineOrganizationInvitationRequestSchema,
)


class AsyncContext:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


def response_json(response):
    return json.loads(response.body.decode("utf-8"))


@pytest.mark.asyncio
async def test_invited_signup_accepts_membership_transactionally(monkeypatch):
    from src.modules.auth.presentation.routers import auth_core_routers as module

    payload = {
        "session_uuid": "session-uuid",
        "user": {
            "uuid": "user-uuid",
            "full_name": "Invited User",
            "email": "invitee@example.com",
            "theme": "light",
            "created_at": None,
        },
    }
    register_execute = AsyncMock(return_value=payload)
    get_user = AsyncMock(
        return_value=SimpleNamespace(id=42, email="invitee@example.com")
    )
    accept_execute = AsyncMock(return_value={"status": "accepted"})

    auth_container = SimpleNamespace(
        register_user_usecase=lambda: SimpleNamespace(execute=register_execute),
        user_domain_service=lambda: SimpleNamespace(get_user_by_email=get_user),
    )
    organization_container = SimpleNamespace(
        accept_organization_invitation_usecase=lambda: SimpleNamespace(
            execute=accept_execute
        )
    )

    monkeypatch.setattr(module, "AuthUOW", lambda _session: AsyncContext())
    monkeypatch.setattr(module, "get_auth_container", lambda _session: auth_container)
    monkeypatch.setattr(
        module, "get_organization_container", lambda _session: organization_container
    )

    request = SimpleNamespace(
        state=SimpleNamespace(ip_address="127.0.0.1", user_agent="pytest")
    )
    body = RegisterRequest(
        full_name="Invited User",
        email="invitee@example.com",
        password="StrongPassword!123",
        invite_token="invite-token",
    )

    response = await module.signup(request, body, object())
    body_json = response_json(response)

    assert response.status_code == 201
    assert body_json["data"]["session_uuid"] == "session-uuid"
    accept_execute.assert_awaited_once()
    call = accept_execute.await_args.kwargs
    assert call["payload"].token == "invite-token"
    assert call["actor_id"] == 42
    assert call["actor_email"] == "invitee@example.com"


@pytest.mark.asyncio
async def test_public_invitation_validation_returns_safe_fields(monkeypatch):
    from src.modules.organization.presentation.routers import organization_routers as module

    invitation = SimpleNamespace(
        email="invitee@example.com",
        organization_id=7,
        role_code="member",
        expires_at=datetime.now(UTC) + timedelta(days=1),
        is_pending=lambda: True,
        is_expired=lambda: False,
    )
    invitation_service = SimpleNamespace(
        hash_invitation_token=lambda token: f"hash:{token}",
        get_invitation_by_token_hash=AsyncMock(return_value=invitation),
    )
    organization_service = SimpleNamespace(
        get_organization_by_id=AsyncMock(
            return_value=SimpleNamespace(name="MailTracko Team")
        )
    )
    container = SimpleNamespace(
        organization_invitation_domain_service=lambda: invitation_service,
        organization_domain_service=lambda: organization_service,
    )

    monkeypatch.setattr(module, "OrganizationUOW", lambda _session: AsyncContext())
    monkeypatch.setattr(module, "get_organization_container", lambda _session: container)

    response = await module.validate_organization_invitation(" invite-token ", object())
    payload = response_json(response)["data"]

    assert payload["email"] == "invitee@example.com"
    assert payload["organization_name"] == "MailTracko Team"
    assert payload["role_code"] == "member"
    assert "token" not in payload


@pytest.mark.asyncio
async def test_public_invitation_decline_uses_token_owner_without_auth(monkeypatch):
    from src.modules.organization.presentation.routers import organization_routers as module

    invitation = SimpleNamespace(email="invitee@example.com")
    invitation_service = SimpleNamespace(
        hash_invitation_token=lambda token: f"hash:{token}",
        get_invitation_by_token_hash=AsyncMock(return_value=invitation),
    )
    decline_execute = AsyncMock(
        return_value={
            "uuid": "invitation-uuid",
            "email": "invitee@example.com",
            "status": "declined",
        }
    )
    container = SimpleNamespace(
        organization_invitation_domain_service=lambda: invitation_service,
        decline_organization_invitation_usecase=lambda: SimpleNamespace(
            execute=decline_execute
        ),
    )

    monkeypatch.setattr(module, "OrganizationUOW", lambda _session: AsyncContext())
    monkeypatch.setattr(module, "get_organization_container", lambda _session: container)

    response = await module.decline_organization_invitation_public(
        DeclineOrganizationInvitationRequestSchema(token="invite-token"), object()
    )
    payload = response_json(response)["data"]

    assert payload["status"] == "declined"
    decline_execute.assert_awaited_once()
    assert decline_execute.await_args.kwargs["actor_id"] is None
    assert decline_execute.await_args.kwargs["actor_email"] == "invitee@example.com"


@pytest.mark.asyncio
async def test_custom_template_detail_returns_body_html(monkeypatch):
    from src.modules.email_template.presentation.routers import (
        email_template_routers as module,
    )

    template = TemplateDetailResponseSchema(
        uuid="template-uuid",
        organization_id=1,
        category_id=None,
        source_template_id=None,
        name="Welcome",
        description=None,
        subject="Hello",
        preheader=None,
        from_name=None,
        from_email=None,
        tags=[],
        template_type="custom",
        status="draft",
        is_active=True,
        is_default=False,
        smart_personalization_enabled=False,
        published_at=None,
        archived_at=None,
        created_by_id=1,
        updated_by_id=1,
        created_at=None,
        updated_at=None,
        body_html="<p>Hello from the editor</p>",
    )
    get_execute = AsyncMock(return_value=template)
    template_container = SimpleNamespace(
        get_template_details_usecase=lambda: SimpleNamespace(execute=get_execute)
    )

    async def set_org_context(request, organization_container):
        request.state.organization_id = 1

    monkeypatch.setattr(module, "EmailTemplateUOW", lambda _session: AsyncContext())
    monkeypatch.setattr(module, "get_email_template_container", lambda _session: template_container)
    monkeypatch.setattr(module, "get_organization_container", lambda _session: object())
    monkeypatch.setattr(module, "_load_current_organization_context", set_org_context)

    request = SimpleNamespace(state=SimpleNamespace(user_id=5))
    response = await module.get_template_details(request, "template-uuid", object())
    payload = response_json(response)["data"]["template"]

    assert payload["body_html"] == "<p>Hello from the editor</p>"
    get_execute.assert_awaited_once_with(
        template_uuid="template-uuid", organization_id=1
    )
