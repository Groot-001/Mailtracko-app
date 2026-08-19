from unittest.mock import AsyncMock

import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def organization_member_domain_service():
    from src.modules.organization.domain.services.organization_member_domain_service import (
        OrganizationMemberDomainService,
    )

    mock_repo = AsyncMock()
    mock_repo.add = AsyncMock()
    mock_repo.get_by_user_id = AsyncMock()
    mock_repo.get_active_by_user_id = AsyncMock()
    mock_repo.get_by_user_and_organization = AsyncMock()
    mock_repo.list_paginated = AsyncMock()

    return OrganizationMemberDomainService(repository=mock_repo)


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


@pytest.mark.asyncio
async def test_add_member_success_when_user_has_no_membership(
    organization_member_domain_service,
):
    member = _make_member()

    organization_member_domain_service.repository.get_by_user_id = AsyncMock(
        return_value=None
    )
    organization_member_domain_service.repository.add = AsyncMock(return_value=member)

    created = await organization_member_domain_service.add_member(member)

    assert created == member

    organization_member_domain_service.repository.get_by_user_id.assert_awaited_once_with(
        user_id=10
    )
    organization_member_domain_service.repository.add.assert_awaited_once_with(member)


@pytest.mark.asyncio
async def test_add_member_with_existing_membership_raises_conflict(
    organization_member_domain_service,
):
    from src.shared.exceptions.base_exceptions import ConflictError

    existing_member = _make_member(organization_id=1, user_id=10)
    new_member = _make_member(organization_id=2, user_id=10)

    organization_member_domain_service.repository.get_by_user_id = AsyncMock(
        return_value=existing_member
    )

    with pytest.raises(ConflictError):
        await organization_member_domain_service.add_member(new_member)

    organization_member_domain_service.repository.get_by_user_id.assert_awaited_once_with(
        user_id=10
    )
    organization_member_domain_service.repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_member_by_user_id_returns_member(
    organization_member_domain_service,
):
    member = _make_member()

    organization_member_domain_service.repository.get_by_user_id = AsyncMock(
        return_value=member
    )

    result = await organization_member_domain_service.get_member_by_user_id(
        user_id=10
    )

    assert result == member

    organization_member_domain_service.repository.get_by_user_id.assert_awaited_once_with(
        user_id=10
    )


@pytest.mark.asyncio
async def test_get_active_member_by_user_id_returns_member(
    organization_member_domain_service,
):
    member = _make_member(status="active")

    organization_member_domain_service.repository.get_active_by_user_id = AsyncMock(
        return_value=member
    )

    result = await organization_member_domain_service.get_active_member_by_user_id(
        user_id=10
    )

    assert result == member

    organization_member_domain_service.repository.get_active_by_user_id.assert_awaited_once_with(
        user_id=10
    )


@pytest.mark.asyncio
async def test_get_member_by_user_and_organization_returns_member(
    organization_member_domain_service,
):
    member = _make_member(organization_id=1, user_id=10)

    organization_member_domain_service.repository.get_by_user_and_organization = (
        AsyncMock(return_value=member)
    )

    result = await organization_member_domain_service.get_member_by_user_and_organization(
        user_id=10,
        organization_id=1,
    )

    assert result == member

    organization_member_domain_service.repository.get_by_user_and_organization.assert_awaited_once_with(
        user_id=10,
        organization_id=1,
    )


@pytest.mark.asyncio
async def test_is_organization_member_returns_true_for_active_member(
    organization_member_domain_service,
):
    member = _make_member(status="active")

    organization_member_domain_service.repository.get_by_user_and_organization = (
        AsyncMock(return_value=member)
    )

    result = await organization_member_domain_service.is_organization_member(
        organization_id=1,
        user_id=10,
    )

    assert result is True

    organization_member_domain_service.repository.get_by_user_and_organization.assert_awaited_once_with(
        user_id=10,
        organization_id=1,
    )


@pytest.mark.asyncio
async def test_is_organization_member_returns_false_when_member_not_found(
    organization_member_domain_service,
):
    organization_member_domain_service.repository.get_by_user_and_organization = (
        AsyncMock(return_value=None)
    )

    result = await organization_member_domain_service.is_organization_member(
        organization_id=1,
        user_id=10,
    )

    assert result is False

    organization_member_domain_service.repository.get_by_user_and_organization.assert_awaited_once_with(
        user_id=10,
        organization_id=1,
    )


@pytest.mark.asyncio
async def test_list_paginated_returns_members_and_total(
    organization_member_domain_service,
):
    member_one = _make_member(id=1, user_id=10, role_code="owner")
    member_two = _make_member(
        id=2,
        uuid="member-uuid-2",
        user_id=20,
        role_code="member",
    )

    organization_member_domain_service.repository.list_paginated = AsyncMock(
        return_value=([member_one, member_two], 2)
    )

    members, total = await organization_member_domain_service.list_paginated(
        organization_id=1,
        status="active",
        limit=50,
        offset=0,
    )

    assert members == [member_one, member_two]
    assert total == 2

    organization_member_domain_service.repository.list_paginated.assert_awaited_once_with(
        organization_id=1,
        status="active",
        limit=50,
        offset=0,
    )