from unittest.mock import AsyncMock

import pytest

from src.modules.organization.domain.entities.organization_activity_entity import (
    OrganizationActivityEntity,
)
from src.modules.organization.domain.services.organization_activity_domain_service import (
    OrganizationActivityDomainService,
)
from src.shared.exceptions.base_exceptions import CreateError, ServerError


def make_activity() -> OrganizationActivityEntity:
    return OrganizationActivityEntity(
        organization_id=1,
        activity_type="invitation_sent",
        title="Invitation sent to test@example.com",
        actor_user_id=1,
        target_user_id=None,
        target_email="test@example.com",
        created_by_id=1,
        updated_by_id=1,
    )


@pytest.mark.asyncio
async def test_create_activity_calls_repository_add():
    repository = AsyncMock()
    activity = make_activity()
    repository.add.return_value = activity

    service = OrganizationActivityDomainService(repository=repository)

    result = await service.create_activity(activity)

    assert result == activity
    repository.add.assert_awaited_once_with(activity)


@pytest.mark.asyncio
async def test_create_activity_wraps_unexpected_error_as_create_error():
    repository = AsyncMock()
    activity = make_activity()
    repository.add.side_effect = Exception("database failed")

    service = OrganizationActivityDomainService(repository=repository)

    with pytest.raises(CreateError):
        await service.create_activity(activity)


@pytest.mark.asyncio
async def test_list_recent_activities_calls_repository():
    repository = AsyncMock()
    activity = make_activity()
    repository.list_by_organization_id.return_value = [activity]

    service = OrganizationActivityDomainService(repository=repository)

    result = await service.list_recent_activities(
        organization_id=1,
        limit=10,
        offset=0,
    )

    assert result == [activity]
    repository.list_by_organization_id.assert_awaited_once_with(
        organization_id=1,
        limit=10,
        offset=0,
    )


@pytest.mark.asyncio
async def test_list_recent_activities_wraps_unexpected_error_as_server_error():
    repository = AsyncMock()
    repository.list_by_organization_id.side_effect = Exception("database failed")

    service = OrganizationActivityDomainService(repository=repository)

    with pytest.raises(ServerError):
        await service.list_recent_activities(
            organization_id=1,
            limit=10,
            offset=0,
        )


@pytest.mark.asyncio
async def test_count_recent_activities_calls_repository():
    repository = AsyncMock()
    repository.count_by_organization_id.return_value = 3

    service = OrganizationActivityDomainService(repository=repository)

    result = await service.count_recent_activities(organization_id=1)

    assert result == 3
    repository.count_by_organization_id.assert_awaited_once_with(
        organization_id=1,
    )


@pytest.mark.asyncio
async def test_count_recent_activities_wraps_unexpected_error_as_server_error():
    repository = AsyncMock()
    repository.count_by_organization_id.side_effect = Exception("database failed")

    service = OrganizationActivityDomainService(repository=repository)

    with pytest.raises(ServerError):
        await service.count_recent_activities(organization_id=1)