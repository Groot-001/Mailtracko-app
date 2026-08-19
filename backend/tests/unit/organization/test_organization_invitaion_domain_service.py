from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio


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


@pytest_asyncio.fixture
async def organization_invitation_domain_service():
    from src.modules.organization.domain.services.organization_invitation_domain_service import (
        OrganizationInvitationDomainService,
    )

    mock_repo = AsyncMock()
    mock_repo.add = AsyncMock()
    mock_repo.update = AsyncMock()
    mock_repo.get_by = AsyncMock()
    mock_repo.get_by_token_hash = AsyncMock()
    mock_repo.get_pending_by_email = AsyncMock()
    mock_repo.list_paginated = AsyncMock()

    return OrganizationInvitationDomainService(repository=mock_repo)


@pytest.mark.asyncio
async def test_create_invitation_success(organization_invitation_domain_service):
    invitation = _make_invitation()

    organization_invitation_domain_service.repository.get_pending_by_email = (
        AsyncMock(return_value=None)
    )
    organization_invitation_domain_service.repository.add = AsyncMock(
        return_value=invitation
    )

    created = await organization_invitation_domain_service.create_invitation(
        invitation
    )

    assert created == invitation

    organization_invitation_domain_service.repository.get_pending_by_email.assert_awaited_once_with(
        organization_id=1,
        email="user@example.com",
    )
    organization_invitation_domain_service.repository.add.assert_awaited_once_with(
        invitation
    )


@pytest.mark.asyncio
async def test_create_invitation_with_existing_pending_raises_conflict(
    organization_invitation_domain_service,
):
    from src.shared.exceptions.base_exceptions import ConflictError

    invitation = _make_invitation()
    existing_invitation = _make_invitation(id=2, uuid="existing-invitation-uuid")

    organization_invitation_domain_service.repository.get_pending_by_email = (
        AsyncMock(return_value=existing_invitation)
    )

    with pytest.raises(ConflictError):
        await organization_invitation_domain_service.create_invitation(invitation)

    organization_invitation_domain_service.repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_invitation_by_uuid_returns_invitation(
    organization_invitation_domain_service,
):
    invitation = _make_invitation()

    organization_invitation_domain_service.repository.get_by = AsyncMock(
        return_value=invitation
    )

    result = await organization_invitation_domain_service.get_invitation_by_uuid(
        invitation_uuid="invitation-uuid"
    )

    assert result == invitation

    organization_invitation_domain_service.repository.get_by.assert_awaited_once_with(
        uuid="invitation-uuid"
    )


@pytest.mark.asyncio
async def test_get_invitation_by_token_hash_returns_invitation(
    organization_invitation_domain_service,
):
    invitation = _make_invitation()

    organization_invitation_domain_service.repository.get_by_token_hash = AsyncMock(
        return_value=invitation
    )

    result = await organization_invitation_domain_service.get_invitation_by_token_hash(
        token_hash="hashed-token"
    )

    assert result == invitation

    organization_invitation_domain_service.repository.get_by_token_hash.assert_awaited_once_with(
        token_hash="hashed-token"
    )


@pytest.mark.asyncio
async def test_list_invitations_paginated_success(
    organization_invitation_domain_service,
):
    invitation_one = _make_invitation(id=1, uuid="invitation-uuid-1")
    invitation_two = _make_invitation(
        id=2,
        uuid="invitation-uuid-2",
        email="admin@example.com",
        role_code="admin",
    )

    organization_invitation_domain_service.repository.list_paginated = AsyncMock(
        return_value=([invitation_one, invitation_two], 2)
    )

    invitations, total = await organization_invitation_domain_service.list_paginated(
        organization_id=1,
        status="pending",
        limit=50,
        offset=0,
    )

    assert invitations == [invitation_one, invitation_two]
    assert total == 2

    organization_invitation_domain_service.repository.list_paginated.assert_awaited_once_with(
        organization_id=1,
        status="pending",
        limit=50,
        offset=0,
    )


@pytest.mark.asyncio
async def test_accept_invitation_success(organization_invitation_domain_service):
    invitation = _make_invitation()

    organization_invitation_domain_service.repository.update = AsyncMock(
        return_value=invitation
    )

    result = await organization_invitation_domain_service.accept_invitation(
        invitation
    )

    assert result == invitation
    assert invitation.status == "accepted"
    assert invitation.accepted_at is not None

    organization_invitation_domain_service.repository.update.assert_awaited_once_with(
        invitation
    )


@pytest.mark.asyncio
async def test_accept_invitation_with_non_pending_status_raises_invalid_error(
    organization_invitation_domain_service,
):
    from src.shared.exceptions.base_exceptions import InvalidError

    invitation = _make_invitation(status="accepted")

    with pytest.raises(InvalidError):
        await organization_invitation_domain_service.accept_invitation(invitation)

    organization_invitation_domain_service.repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_accept_invitation_with_expired_invitation_raises_invalid_error(
    organization_invitation_domain_service,
):
    from src.shared.exceptions.base_exceptions import InvalidError

    invitation = _make_invitation(
        expires_at=datetime.now(UTC) - timedelta(hours=1)
    )

    with pytest.raises(InvalidError):
        await organization_invitation_domain_service.accept_invitation(invitation)

    organization_invitation_domain_service.repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_decline_invitation_success(organization_invitation_domain_service):
    invitation = _make_invitation()

    organization_invitation_domain_service.repository.update = AsyncMock(
        return_value=invitation
    )

    result = await organization_invitation_domain_service.decline_invitation(
        invitation
    )

    assert result == invitation
    assert invitation.status == "declined"
    assert invitation.declined_at is not None

    organization_invitation_domain_service.repository.update.assert_awaited_once_with(
        invitation
    )


@pytest.mark.asyncio
async def test_decline_invitation_with_non_pending_status_raises_invalid_error(
    organization_invitation_domain_service,
):
    from src.shared.exceptions.base_exceptions import InvalidError

    invitation = _make_invitation(status="accepted")

    with pytest.raises(InvalidError):
        await organization_invitation_domain_service.decline_invitation(invitation)

    organization_invitation_domain_service.repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_revoke_invitation_success(organization_invitation_domain_service):
    invitation = _make_invitation()

    organization_invitation_domain_service.repository.update = AsyncMock(
        return_value=invitation
    )

    result = await organization_invitation_domain_service.revoke_invitation(
        invitation
    )

    assert result == invitation
    assert invitation.status == "revoked"
    assert invitation.revoked_at is not None

    organization_invitation_domain_service.repository.update.assert_awaited_once_with(
        invitation
    )


@pytest.mark.asyncio
async def test_revoke_invitation_with_non_pending_status_raises_invalid_error(
    organization_invitation_domain_service,
):
    from src.shared.exceptions.base_exceptions import InvalidError

    invitation = _make_invitation(status="accepted")

    with pytest.raises(InvalidError):
        await organization_invitation_domain_service.revoke_invitation(invitation)

    organization_invitation_domain_service.repository.update.assert_not_awaited()