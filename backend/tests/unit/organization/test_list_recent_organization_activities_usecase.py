from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.modules.organization.application.usecases.core.list_recent_organization_activities_usecase import (
    ListRecentOrganizationActivitiesUseCase,
)
from src.shared.exceptions.base_exceptions import ServerError


class DummyActivity:
    def __init__(
        self,
        uuid: str = "activity-uuid",
        activity_type: str = "invitation_sent",
        title: str = "Invitation sent to test@example.com",
        actor_user_id: int | None = 1,
        target_user_id: int | None = None,
        target_email: str | None = "test@example.com",
        created_at: datetime | None = None,
    ):
        self.uuid = uuid
        self.activity_type = activity_type
        self.title = title
        self.actor_user_id = actor_user_id
        self.target_user_id = target_user_id
        self.target_email = target_email
        self.created_at = created_at or datetime.now(UTC)


@pytest.mark.asyncio
async def test_list_recent_organization_activities_returns_paginated_result():
    service = AsyncMock()
    activity = DummyActivity()

    service.list_recent_activities.return_value = [activity]
    service.count_recent_activities.return_value = 1

    usecase = ListRecentOrganizationActivitiesUseCase(
        organization_activity_domain_service=service,
    )

    result = await usecase.execute(
        organization_id=1,
        limit=10,
        offset=0,
    )

    assert result["total"] == 1
    assert result["limit"] == 10
    assert result["offset"] == 0
    assert len(result["items"]) == 1

    item = result["items"][0]

    assert item["uuid"] == "activity-uuid"
    assert item["activity_type"] == "invitation_sent"
    assert item["title"] == "Invitation sent to test@example.com"
    assert item["actor_user_id"] == 1
    assert item["target_user_id"] is None
    assert item["target_email"] == "test@example.com"
    assert item["created_at"] == activity.created_at

    service.list_recent_activities.assert_awaited_once_with(
        organization_id=1,
        limit=10,
        offset=0,
    )
    service.count_recent_activities.assert_awaited_once_with(
        organization_id=1,
    )


@pytest.mark.asyncio
async def test_list_recent_organization_activities_normalizes_low_limit_and_offset():
    service = AsyncMock()
    service.list_recent_activities.return_value = []
    service.count_recent_activities.return_value = 0

    usecase = ListRecentOrganizationActivitiesUseCase(
        organization_activity_domain_service=service,
    )

    result = await usecase.execute(
        organization_id=1,
        limit=0,
        offset=-5,
    )

    assert result["limit"] == 10
    assert result["offset"] == 0

    service.list_recent_activities.assert_awaited_once_with(
        organization_id=1,
        limit=10,
        offset=0,
    )


@pytest.mark.asyncio
async def test_list_recent_organization_activities_caps_limit_to_50():
    service = AsyncMock()
    service.list_recent_activities.return_value = []
    service.count_recent_activities.return_value = 0

    usecase = ListRecentOrganizationActivitiesUseCase(
        organization_activity_domain_service=service,
    )

    result = await usecase.execute(
        organization_id=1,
        limit=100,
        offset=0,
    )

    assert result["limit"] == 50

    service.list_recent_activities.assert_awaited_once_with(
        organization_id=1,
        limit=50,
        offset=0,
    )


@pytest.mark.asyncio
async def test_list_recent_organization_activities_raises_server_error_on_failure():
    service = AsyncMock()
    service.list_recent_activities.side_effect = Exception("Database failed")

    usecase = ListRecentOrganizationActivitiesUseCase(
        organization_activity_domain_service=service,
    )

    with pytest.raises(ServerError):
        await usecase.execute(
            organization_id=1,
            limit=10,
            offset=0,
        )