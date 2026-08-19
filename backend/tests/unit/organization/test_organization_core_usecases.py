from unittest.mock import AsyncMock

import pytest

from src.shared.exceptions.base_exceptions import ForbiddenError


def _make_organization(**overrides):
    from src.modules.organization.domain.entities.organization_entity import (
        OrganizationEntity,
    )

    data = {
        "id": 1,
        "uuid": "org-uuid",
        "name": "Test Org",
        "website_url": "https://testorg.com",
        "org_size": "1-10 employees",
        "monthly_email_volume": "< 5,000",
        "domain_email": "testorg.com",
        "org_logo": None,
        "description": "Test organization description",
        "industry_sector": "technology",
        "source": "referral",
        "theme": "light",
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


def _make_create_payload(**overrides):
    from src.modules.organization.presentation.schemas.organization_schemas import (
        CreateOrganizationRequestSchema,
    )

    data = {
        "name": "Test Org",
        "website_url": "https://testorg.com",
        "org_size": "1-10 employees",
        "monthly_email_volume": "< 5,000",
        "domain_email": "testorg.com",
        "org_logo": None,
        "description": "Test organization description",
        "industry_sector": "technology",
        "source": "referral",
        "theme": "light",
    }
    data.update(overrides)
    return CreateOrganizationRequestSchema(**data)


def _make_edit_payload(**overrides):
    from src.modules.organization.presentation.schemas.organization_schemas import (
        EditOrganizationRequestSchema,
    )

    return EditOrganizationRequestSchema(**overrides)


@pytest.mark.asyncio
async def test_create_organization_usecase_success():
    from src.modules.organization.application.usecases.core.create_organization_usecase import (
        CreateOrganizationUseCase,
    )

    organization = _make_organization()
    member = _make_member(role_code="owner")

    mock_organization_service = AsyncMock()
    mock_organization_service.create_organization = AsyncMock(
        return_value=organization
    )

    mock_member_service = AsyncMock()
    mock_member_service.get_member_by_user_id = AsyncMock(return_value=None)
    mock_member_service.add_member = AsyncMock(return_value=member)

    usecase = CreateOrganizationUseCase(
        organization_domain_service=mock_organization_service,
        organization_member_domain_service=mock_member_service,
    )

    result = await usecase.execute(
        payload=_make_create_payload(),
        actor_id=10,
    )

    assert result["uuid"] == "org-uuid"
    assert result["name"] == "Test Org"
    assert result["website_url"] == "https://testorg.com"
    assert result["org_size"] == "1-10 employees"
    assert result["domain_email"] == "testorg.com"
    assert result["description"] == "Test organization description"
    assert result["industry_sector"] == "technology"
    assert result["source"] == "referral"
    assert result["theme"] == "light"
    assert result["status"] == "active"
    assert result["owner_id"] == 10
    assert result["member_uuid"] == "member-uuid"
    assert result["role_code"] == "owner"

    mock_member_service.get_member_by_user_id.assert_awaited_once_with(
        user_id=10
    )
    mock_organization_service.create_organization.assert_awaited_once()
    mock_member_service.add_member.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_organization_usecase_raises_when_user_already_has_membership():
    from src.modules.organization.application.usecases.core.create_organization_usecase import (
        CreateOrganizationUseCase,
    )

    existing_member = _make_member()

    mock_organization_service = AsyncMock()

    mock_member_service = AsyncMock()
    mock_member_service.get_member_by_user_id = AsyncMock(
        return_value=existing_member
    )
    mock_member_service.add_member = AsyncMock()

    usecase = CreateOrganizationUseCase(
        organization_domain_service=mock_organization_service,
        organization_member_domain_service=mock_member_service,
    )

    with pytest.raises(ForbiddenError):
        await usecase.execute(
            payload=_make_create_payload(),
            actor_id=10,
        )

    mock_member_service.get_member_by_user_id.assert_awaited_once_with(
        user_id=10
    )
    mock_organization_service.create_organization.assert_not_awaited()
    mock_member_service.add_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_organization_usecase_raises_create_error_when_created_org_has_no_id():
    from src.modules.organization.application.usecases.core.create_organization_usecase import (
        CreateOrganizationUseCase,
    )
    from src.shared.exceptions.base_exceptions import CreateError

    created_organization = _make_organization(id=None)

    mock_organization_service = AsyncMock()
    mock_organization_service.create_organization = AsyncMock(
        return_value=created_organization
    )

    mock_member_service = AsyncMock()
    mock_member_service.get_member_by_user_id = AsyncMock(return_value=None)
    mock_member_service.add_member = AsyncMock()

    usecase = CreateOrganizationUseCase(
        organization_domain_service=mock_organization_service,
        organization_member_domain_service=mock_member_service,
    )

    with pytest.raises(CreateError):
        await usecase.execute(
            payload=_make_create_payload(),
            actor_id=10,
        )

    mock_member_service.get_member_by_user_id.assert_awaited_once_with(
        user_id=10
    )
    mock_organization_service.create_organization.assert_awaited_once()
    mock_member_service.add_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_organization_details_usecase_success():
    from src.modules.organization.application.usecases.core.get_organization_details_usecase import (
        GetOrganizationDetailsUseCase,
    )

    organization = _make_organization()

    mock_organization_service = AsyncMock()
    mock_organization_service.get_organization_by_id = AsyncMock(
        return_value=organization
    )

    usecase = GetOrganizationDetailsUseCase(
        organization_domain_service=mock_organization_service,
    )

    result = await usecase.execute(organization_id=1)

    assert result == organization
    mock_organization_service.get_organization_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_organization_details_usecase_raises_server_error_when_not_found():
    from src.modules.organization.application.usecases.core.get_organization_details_usecase import (
        GetOrganizationDetailsUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_organization_service = AsyncMock()
    mock_organization_service.get_organization_by_id = AsyncMock(return_value=None)

    usecase = GetOrganizationDetailsUseCase(
        organization_domain_service=mock_organization_service,
    )

    with pytest.raises(ServerError):
        await usecase.execute(organization_id=999)


@pytest.mark.asyncio
async def test_edit_organization_details_usecase_success():
    from src.modules.organization.application.usecases.core.edit_organization_details_usecase import (
        EditOrganizationDetailsUseCase,
    )

    organization = _make_organization(name="Old Org")
    owner_member = _make_member(role_code="owner")
    updated_organization = _make_organization(
        name="New Org",
        website_url="https://neworg.com",
        description="Updated description",
    )

    mock_organization_service = AsyncMock()
    mock_organization_service.get_organization_by_uuid = AsyncMock(
        return_value=organization
    )
    mock_organization_service.update_organization = AsyncMock(
        return_value=updated_organization
    )

    mock_member_service = AsyncMock()
    mock_member_service.get_member_by_user_and_organization = AsyncMock(
        return_value=owner_member
    )

    usecase = EditOrganizationDetailsUseCase(
        organization_domain_service=mock_organization_service,
        organization_member_domain_service=mock_member_service,
    )

    result = await usecase.execute(
        organization_uuid="org-uuid",
        payload=_make_edit_payload(
            name="New Org",
            website_url="https://neworg.com",
            description="Updated description",
        ),
        actor_id=10,
    )

    assert result == updated_organization
    assert organization.name == "New Org"
    assert organization.website_url == "https://neworg.com"
    assert organization.description == "Updated description"

    mock_organization_service.get_organization_by_uuid.assert_awaited_once_with(
        "org-uuid"
    )
    mock_member_service.get_member_by_user_and_organization.assert_awaited_once_with(
        organization_id=1,
        user_id=10,
    )
    mock_organization_service.update_organization.assert_awaited_once_with(
        organization,
        10,
    )


@pytest.mark.asyncio
async def test_edit_organization_details_usecase_raises_when_actor_is_not_owner():
    from src.modules.organization.application.usecases.core.edit_organization_details_usecase import (
        EditOrganizationDetailsUseCase,
    )

    organization = _make_organization()
    member = _make_member(role_code="member")

    mock_organization_service = AsyncMock()
    mock_organization_service.get_organization_by_uuid = AsyncMock(
        return_value=organization
    )
    mock_organization_service.update_organization = AsyncMock()

    mock_member_service = AsyncMock()
    mock_member_service.get_member_by_user_and_organization = AsyncMock(
        return_value=member
    )

    usecase = EditOrganizationDetailsUseCase(
        organization_domain_service=mock_organization_service,
        organization_member_domain_service=mock_member_service,
    )

    with pytest.raises(ForbiddenError):
        await usecase.execute(
            organization_uuid="org-uuid",
            payload=_make_edit_payload(name="New Org"),
            actor_id=10,
        )

    mock_organization_service.update_organization.assert_not_awaited()


@pytest.mark.asyncio
async def test_edit_organization_details_usecase_returns_same_org_when_no_fields():
    from src.modules.organization.application.usecases.core.edit_organization_details_usecase import (
        EditOrganizationDetailsUseCase,
    )

    organization = _make_organization()
    owner_member = _make_member(role_code="owner")

    mock_organization_service = AsyncMock()
    mock_organization_service.get_organization_by_uuid = AsyncMock(
        return_value=organization
    )
    mock_organization_service.update_organization = AsyncMock()

    mock_member_service = AsyncMock()
    mock_member_service.get_member_by_user_and_organization = AsyncMock(
        return_value=owner_member
    )

    usecase = EditOrganizationDetailsUseCase(
        organization_domain_service=mock_organization_service,
        organization_member_domain_service=mock_member_service,
    )

    result = await usecase.execute(
        organization_uuid="org-uuid",
        payload=_make_edit_payload(),
        actor_id=10,
    )

    assert result == organization
    mock_organization_service.update_organization.assert_not_awaited()


@pytest.mark.asyncio
async def test_edit_organization_details_usecase_raises_server_error_when_not_found():
    from src.modules.organization.application.usecases.core.edit_organization_details_usecase import (
        EditOrganizationDetailsUseCase,
    )
    from src.shared.exceptions.base_exceptions import ServerError

    mock_organization_service = AsyncMock()
    mock_organization_service.get_organization_by_uuid = AsyncMock(return_value=None)

    mock_member_service = AsyncMock()

    usecase = EditOrganizationDetailsUseCase(
        organization_domain_service=mock_organization_service,
        organization_member_domain_service=mock_member_service,
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            organization_uuid="missing-uuid",
            payload=_make_edit_payload(name="New Org"),
            actor_id=10,
        )


@pytest.mark.asyncio
async def test_list_organization_members_usecase_success():
    from src.modules.organization.application.usecases.core.list_organization_members_usecase import (
        ListOrganizationMembersUseCase,
    )

    member_one = {
        "id": 1,
        "uuid": "member-uuid",
        "organization_id": 1,
        "user_id": 10,
        "role_code": "owner",
        "status": "active",
        "invited_by_id": None,
        "joined_at": None,
        "user": {"uuid": "user-10", "email": "owner@example.com", "full_name": "Owner", "avatar": None, "avatar_bg": None},
    }
    member_two = {
        "id": 2,
        "uuid": "member-uuid-2",
        "organization_id": 1,
        "user_id": 20,
        "role_code": "member",
        "status": "active",
        "invited_by_id": None,
        "joined_at": None,
        "user": {"uuid": "user-20", "email": "member@example.com", "full_name": "Member", "avatar": None, "avatar_bg": None},
    }

    mock_member_service = AsyncMock()
    mock_member_service.list_paginated_with_users = AsyncMock(
        return_value=([member_one, member_two], 2)
    )

    usecase = ListOrganizationMembersUseCase(
        organization_member_domain_service=mock_member_service,
    )

    members, total = await usecase.execute(
        organization_id=1,
        status="active",
        limit=50,
        offset=0,
    )

    assert members == [member_one, member_two]
    assert total == 2

    mock_member_service.list_paginated_with_users.assert_awaited_once_with(
        organization_id=1,
        status="active",
        role=None,
        search=None,
        limit=50,
        offset=0,
    )


@pytest.mark.asyncio
async def test_list_organization_members_usecase_handles_member_without_id():
    from src.modules.organization.application.usecases.core.list_organization_members_usecase import (
        ListOrganizationMembersUseCase,
    )

    member = {
        "id": None,
        "uuid": "member-uuid",
        "organization_id": 1,
        "user_id": 10,
        "role_code": "member",
        "status": "active",
        "invited_by_id": None,
        "joined_at": None,
        "user": None,
    }

    mock_member_service = AsyncMock()
    mock_member_service.list_paginated_with_users = AsyncMock(return_value=([member], 1))

    usecase = ListOrganizationMembersUseCase(
        organization_member_domain_service=mock_member_service,
    )

    members, total = await usecase.execute(
        organization_id=1,
        status=None,
        limit=50,
        offset=0,
    )

    assert members == [member]
    assert total == 1

    mock_member_service.list_paginated_with_users.assert_awaited_once_with(
        organization_id=1,
        status=None,
        role=None,
        search=None,
        limit=50,
        offset=0,
    )





