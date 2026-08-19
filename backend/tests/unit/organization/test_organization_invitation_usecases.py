from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest


def _make_organization(**overrides):
    from src.modules.organization.domain.entities.organization_entity import (
        OrganizationEntity,
    )

    data = {
        "id": 1,
        "uuid": "org-uuid",
        "name": "Test Org",
        "website_url": "https://testorg.com",
        "org_size": "1-10",
        "domain_email": "testorg.com",
        "org_logo": None,
        "description": "Test organization description",
        "industry_sector": "technology",
        "source": "referral",
        "theme": "light",
        "timezone": "UTC",
        "status": "active",
        "owner_id": 10,
        "created_by_id": 10,
    }
    data.update(overrides)
    return OrganizationEntity(**data)


def _make_invitation(**overrides):
    from src.modules.organization.domain.entities.organization_invitation_entity import (
        OrganizationInvitationEntity,
    )

    data = {
        "id": 1,
        "uuid": "invitation-uuid",
        "organization_id": 1,
        "email": "user@example.com",
        "role_code": "member",
        "token_hash": "hashed-token",
        "status": "pending",
        "invited_by_id": 10,
        "expires_at": datetime.now(UTC) + timedelta(days=7),
        "accepted_at": None,
        "declined_at": None,
        "revoked_at": None,
        "created_by_id": 10,
    }
    data.update(overrides)
    return OrganizationInvitationEntity(**data)


def _make_member(**overrides):
    from src.modules.organization.domain.entities.organization_member_entity import (
        OrganizationMemberEntity,
    )

    data = {
        "id": 5,
        "uuid": "member-uuid",
        "organization_id": 1,
        "user_id": 99,
        "role_code": "member",
        "status": "active",
        "invited_by_id": 10,
        "joined_at": None,
        "created_by_id": 99,
    }
    data.update(overrides)
    return OrganizationMemberEntity(**data)


def _make_accept_payload(token="raw-token"):
    from src.modules.organization.presentation.schemas.organization_schemas import (
        AcceptOrganizationInvitationRequestSchema,
    )

    return AcceptOrganizationInvitationRequestSchema(token=token)


def _make_decline_payload(token="raw-token"):
    from src.modules.organization.presentation.schemas.organization_schemas import (
        DeclineOrganizationInvitationRequestSchema,
    )

    return DeclineOrganizationInvitationRequestSchema(token=token)


def _make_invite_payload(**overrides):
    from src.modules.organization.domain.enums.organization_enums import (
        OrganizationRoleCodeEnum,
    )
    from src.modules.organization.presentation.schemas.organization_schemas import (
        InviteOrganizationMemberRequestSchema,
    )

    data = {
        "email": "user@example.com",
        "role_code": OrganizationRoleCodeEnum.MEMBER,
    }
    data.update(overrides)
    return InviteOrganizationMemberRequestSchema(**data)


@pytest.mark.asyncio
async def test_invite_organization_member_usecase_success():
    from src.modules.organization.application.usecases.core.invite_organization_member_usecase import (
        InviteOrganizationMemberUseCase,
    )

    organization = _make_organization()
    owner_member = _make_member(
        id=1,
        user_id=10,
        role_code="owner",
    )
    invitation = _make_invitation(role_code="member")

    mock_organization_service = AsyncMock()
    mock_organization_service.get_organization_by_id = AsyncMock(
        return_value=organization
    )

    mock_invitation_service = AsyncMock()
    mock_invitation_service.generate_invitation_token = Mock(return_value="raw-token")
    mock_invitation_service.hash_invitation_token = Mock(return_value="hashed-token")
    mock_invitation_service.create_invitation = AsyncMock(return_value=invitation)
    mock_invitation_service.get_pending_invitation_by_email = AsyncMock(return_value=None)

    mock_member_service = AsyncMock()
    mock_member_service.get_member_by_user_and_organization = AsyncMock(
        return_value=owner_member
    )
    mock_member_service.list_paginated_with_users = AsyncMock(return_value=([], 0))

    usecase = InviteOrganizationMemberUseCase(
        organization_domain_service=mock_organization_service,
        organization_invitation_domain_service=mock_invitation_service,
        organization_member_domain_service=mock_member_service,
    )

    result = await usecase.execute(
        organization_id=1,
        payload=_make_invite_payload(),
        actor_id=10,
    )

    assert result["uuid"] == "invitation-uuid"
    assert result["email"] == "user@example.com"
    assert result["role_code"] == "member"
    assert result["status"] == "pending"
    assert result["expires_at"] == invitation.expires_at

    mock_organization_service.get_organization_by_id.assert_awaited_once_with(
        organization_id=1
    )
    mock_member_service.get_member_by_user_and_organization.assert_awaited_once_with(
        organization_id=1,
        user_id=10,
    )
    mock_invitation_service.generate_invitation_token.assert_called_once()
    mock_invitation_service.hash_invitation_token.assert_called_once_with("raw-token")
    mock_invitation_service.create_invitation.assert_awaited_once()


@pytest.mark.asyncio
async def test_invite_organization_member_rejects_existing_member_email():
    from src.modules.organization.application.usecases.core.invite_organization_member_usecase import (
        InviteOrganizationMemberUseCase,
    )
    from src.shared.exceptions.base_exceptions import ConflictError

    organization = _make_organization()
    owner_member = _make_member(id=1, user_id=10, role_code="owner")
    mock_organization_service = AsyncMock()
    mock_organization_service.get_organization_by_id = AsyncMock(return_value=organization)
    mock_invitation_service = AsyncMock()
    mock_invitation_service.create_invitation = AsyncMock()
    mock_member_service = AsyncMock()
    mock_member_service.get_member_by_user_and_organization = AsyncMock(return_value=owner_member)
    mock_member_service.list_paginated_with_users = AsyncMock(
        return_value=([{"user": {"email": "User@Example.com"}}], 1)
    )

    usecase = InviteOrganizationMemberUseCase(
        organization_domain_service=mock_organization_service,
        organization_invitation_domain_service=mock_invitation_service,
        organization_member_domain_service=mock_member_service,
    )

    with pytest.raises(ConflictError, match="already exists"):
        await usecase.execute(organization_id=1, payload=_make_invite_payload(), actor_id=10)
    mock_invitation_service.create_invitation.assert_not_awaited()


@pytest.mark.asyncio
async def test_invite_organization_member_rejects_existing_pending_invitation():
    from src.modules.organization.application.usecases.core.invite_organization_member_usecase import (
        InviteOrganizationMemberUseCase,
    )
    from src.shared.exceptions.base_exceptions import ConflictError

    organization = _make_organization()
    owner_member = _make_member(id=1, user_id=10, role_code="owner")
    pending = _make_invitation(email="user@example.com")
    mock_organization_service = AsyncMock()
    mock_organization_service.get_organization_by_id = AsyncMock(return_value=organization)
    mock_invitation_service = AsyncMock()
    mock_invitation_service.get_pending_invitation_by_email = AsyncMock(return_value=pending)
    mock_invitation_service.create_invitation = AsyncMock()
    mock_member_service = AsyncMock()
    mock_member_service.get_member_by_user_and_organization = AsyncMock(return_value=owner_member)
    mock_member_service.list_paginated_with_users = AsyncMock(return_value=([], 0))

    usecase = InviteOrganizationMemberUseCase(
        organization_domain_service=mock_organization_service,
        organization_invitation_domain_service=mock_invitation_service,
        organization_member_domain_service=mock_member_service,
    )

    with pytest.raises(ConflictError, match="already pending"):
        await usecase.execute(organization_id=1, payload=_make_invite_payload(), actor_id=10)
    mock_invitation_service.create_invitation.assert_not_awaited()


@pytest.mark.asyncio
async def test_invite_organization_member_usecase_raises_when_actor_is_not_owner():
    from src.modules.organization.application.usecases.core.invite_organization_member_usecase import (
        InviteOrganizationMemberUseCase,
    )
    from src.shared.exceptions.base_exceptions import ForbiddenError

    organization = _make_organization()
    member = _make_member(
        user_id=10,
        role_code="member",
    )

    mock_organization_service = AsyncMock()
    mock_organization_service.get_organization_by_id = AsyncMock(
        return_value=organization
    )

    mock_invitation_service = AsyncMock()
    mock_invitation_service.create_invitation = AsyncMock()

    mock_member_service = AsyncMock()
    mock_member_service.get_member_by_user_and_organization = AsyncMock(
        return_value=member
    )

    usecase = InviteOrganizationMemberUseCase(
        organization_domain_service=mock_organization_service,
        organization_invitation_domain_service=mock_invitation_service,
        organization_member_domain_service=mock_member_service,
    )

    with pytest.raises(ForbiddenError):
        await usecase.execute(
            organization_id=1,
            payload=_make_invite_payload(),
            actor_id=10,
        )

    mock_organization_service.get_organization_by_id.assert_awaited_once_with(
        organization_id=1
    )
    mock_invitation_service.create_invitation.assert_not_awaited()


@pytest.mark.asyncio
async def test_accept_organization_invitation_usecase_success():
    from src.modules.organization.application.usecases.core.accept_organization_invitation_usecase import (
        AcceptOrganizationInvitationUseCase,
    )

    invitation = _make_invitation(role_code="member")
    accepted_invitation = _make_invitation(status="accepted", role_code="member")
    member = _make_member(
        id=5,
        uuid="member-uuid",
        user_id=99,
        role_code="member",
    )

    mock_invitation_service = AsyncMock()
    mock_invitation_service.hash_invitation_token = Mock(return_value="hashed-token")
    mock_invitation_service.get_invitation_by_token_hash = AsyncMock(
        return_value=invitation
    )
    mock_invitation_service.accept_invitation = AsyncMock(
        return_value=accepted_invitation
    )

    mock_member_service = AsyncMock()
    mock_member_service.get_member_by_user_id = AsyncMock(return_value=None)
    mock_member_service.add_member = AsyncMock(return_value=member)

    usecase = AcceptOrganizationInvitationUseCase(
        organization_invitation_domain_service=mock_invitation_service,
        organization_member_domain_service=mock_member_service,
    )

    result = await usecase.execute(
        payload=_make_accept_payload(),
        actor_id=99,
        actor_email="user@example.com",
    )

    assert result["uuid"] == "invitation-uuid"
    assert result["email"] == "user@example.com"
    assert result["status"] == "accepted"
    assert result["organization_id"] == 1
    assert result["role_code"] == "member"
    assert result["member_uuid"] == "member-uuid"

    mock_member_service.get_member_by_user_id.assert_awaited_once_with(
        user_id=99
    )
    mock_invitation_service.accept_invitation.assert_awaited_once_with(invitation)
    mock_member_service.add_member.assert_awaited_once()


@pytest.mark.asyncio
async def test_accept_organization_invitation_usecase_raises_create_error_when_invitation_not_found():
    from src.modules.organization.application.usecases.core.accept_organization_invitation_usecase import (
        AcceptOrganizationInvitationUseCase,
    )
    from src.shared.exceptions.base_exceptions import CreateError

    mock_invitation_service = AsyncMock()
    mock_invitation_service.hash_invitation_token = Mock(return_value="hashed-token")
    mock_invitation_service.get_invitation_by_token_hash = AsyncMock(return_value=None)

    usecase = AcceptOrganizationInvitationUseCase(
        organization_invitation_domain_service=mock_invitation_service,
        organization_member_domain_service=AsyncMock(),
    )

    with pytest.raises(CreateError):
        await usecase.execute(
            payload=_make_accept_payload(),
            actor_id=99,
            actor_email="user@example.com",
        )


@pytest.mark.asyncio
async def test_accept_organization_invitation_usecase_raises_create_error_when_email_mismatch():
    from src.modules.organization.application.usecases.core.accept_organization_invitation_usecase import (
        AcceptOrganizationInvitationUseCase,
    )
    from src.shared.exceptions.base_exceptions import CreateError

    invitation = _make_invitation(email="user@example.com")

    mock_invitation_service = AsyncMock()
    mock_invitation_service.hash_invitation_token = Mock(return_value="hashed-token")
    mock_invitation_service.get_invitation_by_token_hash = AsyncMock(
        return_value=invitation
    )

    usecase = AcceptOrganizationInvitationUseCase(
        organization_invitation_domain_service=mock_invitation_service,
        organization_member_domain_service=AsyncMock(),
    )

    with pytest.raises(CreateError):
        await usecase.execute(
            payload=_make_accept_payload(),
            actor_id=99,
            actor_email="other@example.com",
        )


@pytest.mark.asyncio
async def test_accept_organization_invitation_usecase_raises_create_error_when_user_already_has_organization():
    from src.modules.organization.application.usecases.core.accept_organization_invitation_usecase import (
        AcceptOrganizationInvitationUseCase,
    )
    from src.shared.exceptions.base_exceptions import CreateError

    invitation = _make_invitation()
    existing_member = _make_member(user_id=99)

    mock_invitation_service = AsyncMock()
    mock_invitation_service.hash_invitation_token = Mock(return_value="hashed-token")
    mock_invitation_service.get_invitation_by_token_hash = AsyncMock(
        return_value=invitation
    )
    mock_invitation_service.accept_invitation = AsyncMock()

    mock_member_service = AsyncMock()
    mock_member_service.get_member_by_user_id = AsyncMock(
        return_value=existing_member
    )
    mock_member_service.add_member = AsyncMock()

    usecase = AcceptOrganizationInvitationUseCase(
        organization_invitation_domain_service=mock_invitation_service,
        organization_member_domain_service=mock_member_service,
    )

    with pytest.raises(CreateError):
        await usecase.execute(
            payload=_make_accept_payload(),
            actor_id=99,
            actor_email="user@example.com",
        )

    mock_invitation_service.accept_invitation.assert_not_awaited()
    mock_member_service.add_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_decline_organization_invitation_usecase_success():
    from src.modules.organization.application.usecases.core.decline_organization_invitation_usecase import (
        DeclineOrganizationInvitationUseCase,
    )

    invitation = _make_invitation()
    declined_invitation = _make_invitation(status="declined")

    mock_invitation_service = AsyncMock()
    mock_invitation_service.hash_invitation_token = Mock(return_value="hashed-token")
    mock_invitation_service.get_invitation_by_token_hash = AsyncMock(
        return_value=invitation
    )
    mock_invitation_service.decline_invitation = AsyncMock(
        return_value=declined_invitation
    )

    usecase = DeclineOrganizationInvitationUseCase(
        organization_invitation_domain_service=mock_invitation_service,
    )

    result = await usecase.execute(
        payload=_make_decline_payload(),
        actor_id=99,
        actor_email="user@example.com",
    )

    assert result["uuid"] == "invitation-uuid"
    assert result["email"] == "user@example.com"
    assert result["status"] == "declined"

    mock_invitation_service.decline_invitation.assert_awaited_once_with(invitation)


@pytest.mark.asyncio
async def test_revoke_organization_invitation_usecase_success():
    from src.modules.organization.application.usecases.core.revoke_organization_invitation_usecase import (
        RevokeOrganizationInvitationUseCase,
    )

    owner_member = _make_member(
        id=1,
        user_id=10,
        role_code="owner",
    )
    invitation = _make_invitation()
    revoked_invitation = _make_invitation(status="revoked")

    mock_invitation_service = AsyncMock()
    mock_invitation_service.get_invitation_by_uuid = AsyncMock(
        return_value=invitation
    )
    mock_invitation_service.revoke_invitation = AsyncMock(
        return_value=revoked_invitation
    )

    mock_member_service = AsyncMock()
    mock_member_service.get_member_by_user_and_organization = AsyncMock(
        return_value=owner_member
    )

    usecase = RevokeOrganizationInvitationUseCase(
        organization_invitation_domain_service=mock_invitation_service,
        organization_member_domain_service=mock_member_service,
    )

    result = await usecase.execute(
        organization_id=1,
        invitation_uuid="invitation-uuid",
        actor_id=10,
    )

    assert result["uuid"] == "invitation-uuid"
    assert result["email"] == "user@example.com"
    assert result["role_code"] == "member"
    assert result["status"] == "revoked"

    mock_member_service.get_member_by_user_and_organization.assert_awaited_once_with(
        organization_id=1,
        user_id=10,
    )
    mock_invitation_service.revoke_invitation.assert_awaited_once_with(invitation)


@pytest.mark.asyncio
async def test_revoke_organization_invitation_usecase_raises_when_actor_is_not_owner():
    from src.modules.organization.application.usecases.core.revoke_organization_invitation_usecase import (
        RevokeOrganizationInvitationUseCase,
    )
    from src.shared.exceptions.base_exceptions import ForbiddenError

    member = _make_member(
        user_id=10,
        role_code="member",
    )

    mock_invitation_service = AsyncMock()
    mock_invitation_service.get_invitation_by_uuid = AsyncMock()
    mock_invitation_service.revoke_invitation = AsyncMock()

    mock_member_service = AsyncMock()
    mock_member_service.get_member_by_user_and_organization = AsyncMock(
        return_value=member
    )

    usecase = RevokeOrganizationInvitationUseCase(
        organization_invitation_domain_service=mock_invitation_service,
        organization_member_domain_service=mock_member_service,
    )

    with pytest.raises(ForbiddenError):
        await usecase.execute(
            organization_id=1,
            invitation_uuid="invitation-uuid",
            actor_id=10,
        )

    mock_invitation_service.get_invitation_by_uuid.assert_not_awaited()
    mock_invitation_service.revoke_invitation.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_organization_invitations_usecase_success():
    from src.modules.organization.application.usecases.core.list_organization_invitations_usecase import (
        ListOrganizationInvitationsUseCase,
    )

    invitations = [
        _make_invitation(id=1, uuid="invitation-uuid-1"),
        _make_invitation(id=2, uuid="invitation-uuid-2", email="admin@example.com"),
    ]

    mock_invitation_service = AsyncMock()
    mock_invitation_service.list_paginated = AsyncMock(
        return_value=(invitations, 2)
    )

    usecase = ListOrganizationInvitationsUseCase(
        organization_invitation_domain_service=mock_invitation_service,
    )

    result_invitations, total = await usecase.execute(
        organization_id=1,
        status="pending",
        limit=50,
        offset=0,
    )

    assert result_invitations == invitations
    assert total == 2

    mock_invitation_service.list_paginated.assert_awaited_once_with(
        organization_id=1,
        status="pending",
        limit=50,
        offset=0,
    )
@pytest.mark.asyncio
async def test_resend_organization_invitation_refreshes_token_expiry_and_publishes_event(monkeypatch):
    from src.modules.organization.application.usecases.core.resend_organization_invitation_usecase import (
        ResendOrganizationInvitationUseCase,
    )
    from src.modules.organization.domain.events.organization_domain_events import (
        OrganizationInvitationCreatedEvent,
    )

    organization = _make_organization()
    owner_member = _make_member(id=1, user_id=10, role_code="owner")
    invitation = _make_invitation()
    original_expiry = invitation.expires_at

    organization_service = AsyncMock()
    organization_service.get_organization_by_id = AsyncMock(return_value=organization)

    invitation_service = AsyncMock()
    invitation_service.get_invitation_by_uuid = AsyncMock(return_value=invitation)
    invitation_service.generate_invitation_token = Mock(return_value="fresh-raw-token")
    invitation_service.hash_invitation_token = Mock(return_value="fresh-hash")

    async def refresh(entity, *, token_hash, expires_at):
        entity.refresh_for_resend(token_hash=token_hash, expires_at=expires_at)
        return entity

    invitation_service.resend_invitation = AsyncMock(side_effect=refresh)

    member_service = AsyncMock()
    member_service.get_member_by_user_and_organization = AsyncMock(return_value=owner_member)

    publish = AsyncMock()
    monkeypatch.setattr(
        "src.modules.organization.application.usecases.core.resend_organization_invitation_usecase.mediator.publish",
        publish,
    )

    result = await ResendOrganizationInvitationUseCase(
        organization_domain_service=organization_service,
        organization_invitation_domain_service=invitation_service,
        organization_member_domain_service=member_service,
    ).execute(organization_id=1, invitation_uuid="invitation-uuid", actor_id=10)

    assert result["uuid"] == "invitation-uuid"
    assert invitation.token_hash == "fresh-hash"
    assert invitation.expires_at > original_expiry
    assert invitation.updated_at is not None
    invitation_service.hash_invitation_token.assert_called_once_with("fresh-raw-token")
    invitation_service.resend_invitation.assert_awaited_once()
    publish.assert_awaited_once()
    event = publish.await_args.args[0]
    assert isinstance(event, OrganizationInvitationCreatedEvent)
    assert event.token == "fresh-raw-token"
    assert event.invitee_email == "user@example.com"
    assert publish.await_args.kwargs == {"raise_on_error": True}


@pytest.mark.asyncio
async def test_resend_organization_invitation_rejects_non_pending_invite():
    from src.modules.organization.application.usecases.core.resend_organization_invitation_usecase import (
        ResendOrganizationInvitationUseCase,
    )
    from src.shared.exceptions.base_exceptions import InvalidError

    organization_service = AsyncMock()
    invitation_service = AsyncMock()
    invitation_service.get_invitation_by_uuid = AsyncMock(
        return_value=_make_invitation(status="accepted")
    )
    member_service = AsyncMock()
    member_service.get_member_by_user_and_organization = AsyncMock(
        return_value=_make_member(id=1, user_id=10, role_code="owner")
    )

    usecase = ResendOrganizationInvitationUseCase(
        organization_domain_service=organization_service,
        organization_invitation_domain_service=invitation_service,
        organization_member_domain_service=member_service,
    )

    with pytest.raises(InvalidError, match="Only pending invitation"):
        await usecase.execute(organization_id=1, invitation_uuid="invitation-uuid", actor_id=10)

    invitation_service.resend_invitation.assert_not_awaited()
