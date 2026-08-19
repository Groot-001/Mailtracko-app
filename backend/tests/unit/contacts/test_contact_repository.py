# Test compatibility update: use the current Contacts metadata-based entity contract.
from unittest.mock import AsyncMock, MagicMock
import pytest

from src.modules.contacts.domain.entities.contact_entity import ContactEntity
from src.modules.contacts.infrastructure.repositories.contact_repository_impl import ContactRepositoryImpl


@pytest.mark.asyncio
async def test_bulk_upsert_handles_duplicate_emails_in_batch():
    session = MagicMock()
    # Mock result of execute (SELECT for existing emails)
    result_mock = MagicMock()
    result_mock.mappings.return_value.all.return_value = []  # No existing contacts in DB
    session.execute = AsyncMock(return_value=result_mock)

    repo = ContactRepositoryImpl(session)

    # Mock add and update on repo
    added_counter = 0

    async def mock_add(entity: ContactEntity):
        nonlocal added_counter
        added_counter += 1
        return ContactEntity(
            id=added_counter,
            organization_id=entity.organization_id,
            contact_list_id=entity.contact_list_id,
            email=entity.email,
            metadata=dict(entity.metadata or {}),
        )

    async def mock_update(entity: ContactEntity):
        return entity

    repo.add = AsyncMock(side_effect=mock_add)
    repo.update = AsyncMock(side_effect=mock_update)

    # 2 entities with the EXACT same email '2011' in the same batch
    e1 = ContactEntity(
        organization_id=1,
        contact_list_id=3,
        email="2011",
        metadata={"first_name": "Row 1"},
    )
    e2 = ContactEntity(
        organization_id=1,
        contact_list_id=3,
        email="2011",
        metadata={"first_name": "Row 2"},
    )

    created, updated_count = await repo.bulk_upsert([e1, e2])

    assert len(created) == 2
    assert updated_count == 1  # The 2nd entity updated the 1st
    assert repo.add.call_count == 1  # Add called only once
    assert repo.update.call_count == 1  # Update called for 2nd row
