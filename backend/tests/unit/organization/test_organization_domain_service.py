from unittest.mock import AsyncMock

import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def organization_domain_service():
    from src.modules.organization.domain.services.organization_domain_service import (
        OrganizationDomainService,
    )

    mock_repo = AsyncMock()
    mock_repo.add = AsyncMock()
    mock_repo.update = AsyncMock()
    mock_repo.get_by = AsyncMock()
    mock_repo.get_active_by_owner_id = AsyncMock()

    return OrganizationDomainService(repository=mock_repo)


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
        "status": "active",
        "owner_id": 10,
        "created_by_id": 10,
    }
    data.update(overrides)
    return OrganizationEntity(**data)


@pytest.mark.asyncio
async def test_create_organization_success(organization_domain_service):
    organization = _make_organization(status="active")

    organization_domain_service.repository.get_active_by_owner_id = AsyncMock(
        return_value=None
    )
    organization_domain_service.repository.add = AsyncMock(return_value=organization)

    created = await organization_domain_service.create_organization(organization)

    assert created == organization
    assert created.status == "active"

    organization_domain_service.repository.get_active_by_owner_id.assert_awaited_once_with(
        owner_id=10
    )
    organization_domain_service.repository.add.assert_awaited_once_with(organization)


@pytest.mark.asyncio
async def test_create_organization_when_owner_already_has_active_org_raises_conflict_error(
    organization_domain_service,
):
    from src.shared.exceptions.base_exceptions import ConflictError

    organization = _make_organization()
    existing_organization = _make_organization(id=2, uuid="existing-org-uuid")

    organization_domain_service.repository.get_active_by_owner_id = AsyncMock(
        return_value=existing_organization
    )

    with pytest.raises(ConflictError):
        await organization_domain_service.create_organization(organization)

    organization_domain_service.repository.get_active_by_owner_id.assert_awaited_once_with(
        owner_id=10
    )
    organization_domain_service.repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_activate_organization_success(organization_domain_service):
    organization = _make_organization(status="suspended")
    updated_organization = _make_organization(status="active")

    organization_domain_service.repository.get_by = AsyncMock(return_value=organization)
    organization_domain_service.repository.update = AsyncMock(
        return_value=updated_organization
    )

    result = await organization_domain_service.activate_organization(
        organization_id=1
    )

    assert result.status == "active"

    organization_domain_service.repository.get_by.assert_awaited_once_with(
        id=1,
        deleted_at=None,
    )
    organization_domain_service.repository.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_activate_organization_not_found_raises_invalid_error(
    organization_domain_service,
):
    from src.shared.exceptions.base_exceptions import InvalidError

    organization_domain_service.repository.get_by = AsyncMock(return_value=None)

    with pytest.raises(InvalidError):
        await organization_domain_service.activate_organization(organization_id=999)

    organization_domain_service.repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_organization_success(organization_domain_service):
    organization = _make_organization()
    organization_domain_service.repository.update = AsyncMock(return_value=organization)

    result = await organization_domain_service.update_organization(
        organization_entity=organization,
        actor_id=20,
    )

    assert result == organization
    assert organization.updated_by_id == 20

    organization_domain_service.repository.update.assert_awaited_once_with(
        organization
    )


@pytest.mark.asyncio
async def test_get_organization_by_id_success(organization_domain_service):
    organization = _make_organization()

    organization_domain_service.repository.get_by = AsyncMock(return_value=organization)

    result = await organization_domain_service.get_organization_by_id(
        organization_id=1
    )

    assert result == organization

    organization_domain_service.repository.get_by.assert_awaited_once_with(
        id=1,
        deleted_at=None,
    )


@pytest.mark.asyncio
async def test_get_organization_by_uuid_success(organization_domain_service):
    organization = _make_organization()

    organization_domain_service.repository.get_by = AsyncMock(return_value=organization)

    result = await organization_domain_service.get_organization_by_uuid("org-uuid")

    assert result == organization

    organization_domain_service.repository.get_by.assert_awaited_once_with(
        uuid="org-uuid",
        deleted_at=None,
    )


@pytest.mark.asyncio
async def test_get_active_organization_by_owner_id_success(
    organization_domain_service,
):
    organization = _make_organization(owner_id=10)

    organization_domain_service.repository.get_active_by_owner_id = AsyncMock(
        return_value=organization
    )

    result = await organization_domain_service.get_active_organization_by_owner_id(
        owner_id=10
    )

    assert result == organization

    organization_domain_service.repository.get_active_by_owner_id.assert_awaited_once_with(
        owner_id=10
    )