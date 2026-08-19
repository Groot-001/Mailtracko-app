from unittest.mock import AsyncMock

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


def _make_member(**overrides):
    from src.modules.organization.domain.entities.organization_member_entity import (
        OrganizationMemberEntity,
    )

    data = {
        "id": 1,
        "uuid": "member-uuid",
        "organization_id": 1,
        "user_id": 10,
        "role_code": "owner",
        "status": "active",
        "invited_by_id": None,
        "joined_at": None,
        "created_by_id": 10,
    }
    data.update(overrides)
    return OrganizationMemberEntity(**data)


class DummyInvitation:
    uuid = "invitation-uuid"


@pytest.mark.asyncio
async def test_onboarding_status_when_user_has_no_membership():
    from src.modules.organization.application.usecases.core.get_organization_onboarding_status_usecase import (
        GetOrganizationOnboardingStatusUseCase,
    )

    mock_organization_service = AsyncMock()

    mock_member_service = AsyncMock()
    mock_member_service.get_active_member_by_user_id = AsyncMock(return_value=None)

    mock_invitation_service = AsyncMock()
    mock_invitation_service.get_pending_invitation_by_email_global = AsyncMock(
        return_value=[]
    )

    usecase = GetOrganizationOnboardingStatusUseCase(
        organization_domain_service=mock_organization_service,
        organization_member_domain_service=mock_member_service,
        organization_invitation_domain_service=mock_invitation_service,
    )

    result = await usecase.execute(
        user_id=10,
        actor_email="user@example.com",
    )

    assert result["has_completed_onboarding"] is False
    assert result["needs_onboarding"] is True
    assert result["has_pending_invitation"] is False
    assert result["invitation_uuid"] is None
    assert result["organization_uuid"] is None
    assert result["role_code"] is None

    mock_member_service.get_active_member_by_user_id.assert_awaited_once_with(
        user_id=10
    )
    mock_invitation_service.get_pending_invitation_by_email_global.assert_awaited_once_with(
        email="user@example.com"
    )
    mock_organization_service.get_organization_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_onboarding_status_when_user_has_pending_invitation():
    from src.modules.organization.application.usecases.core.get_organization_onboarding_status_usecase import (
        GetOrganizationOnboardingStatusUseCase,
    )

    mock_organization_service = AsyncMock()

    mock_member_service = AsyncMock()
    mock_member_service.get_active_member_by_user_id = AsyncMock(return_value=None)

    mock_invitation_service = AsyncMock()
    mock_invitation_service.get_pending_invitation_by_email_global = AsyncMock(
        return_value=[DummyInvitation()]
    )

    usecase = GetOrganizationOnboardingStatusUseCase(
        organization_domain_service=mock_organization_service,
        organization_member_domain_service=mock_member_service,
        organization_invitation_domain_service=mock_invitation_service,
    )

    result = await usecase.execute(
        user_id=10,
        actor_email="user@example.com",
    )

    assert result["has_completed_onboarding"] is False
    assert result["needs_onboarding"] is False
    assert result["has_pending_invitation"] is True
    assert result["invitation_uuid"] == "invitation-uuid"
    assert result["organization_uuid"] is None
    assert result["role_code"] is None

    mock_member_service.get_active_member_by_user_id.assert_awaited_once_with(
        user_id=10
    )
    mock_invitation_service.get_pending_invitation_by_email_global.assert_awaited_once_with(
        email="user@example.com"
    )
    mock_organization_service.get_organization_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_onboarding_status_when_user_has_membership():
    from src.modules.organization.application.usecases.core.get_organization_onboarding_status_usecase import (
        GetOrganizationOnboardingStatusUseCase,
    )

    member = _make_member(role_code="owner")
    organization = _make_organization(uuid="org-uuid")

    mock_member_service = AsyncMock()
    mock_member_service.get_active_member_by_user_id = AsyncMock(
        return_value=member
    )

    mock_organization_service = AsyncMock()
    mock_organization_service.get_organization_by_id = AsyncMock(
        return_value=organization
    )

    mock_invitation_service = AsyncMock()
    mock_invitation_service.get_pending_invitation_by_email_global = AsyncMock(
        return_value=[]
    )

    usecase = GetOrganizationOnboardingStatusUseCase(
        organization_domain_service=mock_organization_service,
        organization_member_domain_service=mock_member_service,
        organization_invitation_domain_service=mock_invitation_service,
    )

    result = await usecase.execute(
        user_id=10,
        actor_email="user@example.com",
    )

    assert result["has_completed_onboarding"] is True
    assert result["needs_onboarding"] is False
    assert result["has_pending_invitation"] is False
    assert result["invitation_uuid"] is None
    assert result["organization_uuid"] == "org-uuid"
    assert result["role_code"] == "owner"

    mock_member_service.get_active_member_by_user_id.assert_awaited_once_with(
        user_id=10
    )
    mock_organization_service.get_organization_by_id.assert_awaited_once_with(
        organization_id=1
    )
    mock_invitation_service.get_pending_invitation_by_email_global.assert_not_awaited()


@pytest.mark.asyncio
async def test_onboarding_status_when_membership_has_missing_organization():
    from src.modules.organization.application.usecases.core.get_organization_onboarding_status_usecase import (
        GetOrganizationOnboardingStatusUseCase,
    )

    member = _make_member()

    mock_member_service = AsyncMock()
    mock_member_service.get_active_member_by_user_id = AsyncMock(
        return_value=member
    )

    mock_organization_service = AsyncMock()
    mock_organization_service.get_organization_by_id = AsyncMock(return_value=None)

    mock_invitation_service = AsyncMock()
    mock_invitation_service.get_pending_invitation_by_email_global = AsyncMock(
        return_value=[]
    )

    usecase = GetOrganizationOnboardingStatusUseCase(
        organization_domain_service=mock_organization_service,
        organization_member_domain_service=mock_member_service,
        organization_invitation_domain_service=mock_invitation_service,
    )

    result = await usecase.execute(
        user_id=10,
        actor_email="user@example.com",
    )

    assert result["has_completed_onboarding"] is True
    assert result["needs_onboarding"] is False
    assert result["has_pending_invitation"] is False
    assert result["invitation_uuid"] is None
    assert result["organization_uuid"] is None
    assert result["role_code"] == "owner"

    mock_member_service.get_active_member_by_user_id.assert_awaited_once_with(
        user_id=10
    )
    mock_organization_service.get_organization_by_id.assert_awaited_once_with(
        organization_id=1
    )