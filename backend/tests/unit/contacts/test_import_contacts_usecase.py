# Test compatibility update: use the current Contacts domain-service constructor contract.
from unittest.mock import AsyncMock, MagicMock
import pytest

from src.modules.contacts.application.usecases.core.import_contacts_usecase import ImportContactsUseCase
from src.modules.contacts.domain.entities.contact_entity import ContactEntity
from src.modules.contacts.domain.entities.contact_list_entity import ContactListEntity
from src.shared.exceptions.base_exceptions import DomainError, ForbiddenError


@pytest.mark.asyncio
async def test_import_contacts_success():
    service = MagicMock()
    contact_list = ContactListEntity(
        id=1,
        uuid="50ce2993-12a2-43aa-a557-502c951296e8",
        organization_id=10,
        name="Test List",
        field_definitions=[],
    )
    service.get_by_uuid = AsyncMock(return_value=contact_list)
    service.update_field_definitions = AsyncMock(return_value=contact_list)

    contact_domain_service = MagicMock()
    contact_domain_service.get_existing_by_emails = AsyncMock(return_value=[])
    contact1 = ContactEntity(id=1, organization_id=10, contact_list_id=1, email="john@example.com")
    contact2 = ContactEntity(id=2, organization_id=10, contact_list_id=1, email="jane@example.com")
    contact_domain_service.bulk_upsert = AsyncMock(
        return_value=([contact1, contact2], 0)
    )

    import_log_repo = MagicMock()
    import_log_repo.add = AsyncMock()
    contact_activity_repo = MagicMock()
    contact_activity_repo.add = AsyncMock()

    usecase = ImportContactsUseCase(
        contact_list_domain_service=service,
        contact_domain_service=contact_domain_service,
        import_log_repo=import_log_repo,
        contact_activity_repo=contact_activity_repo,
    )

    csv_data = b"Email,First_Name,Last_Name,CustomField\njohn@example.com,John,Doe,Val1\njane@example.com,Jane,Doe,Val2\n"

    result = await usecase.execute(
        list_uuid="50ce2993-12a2-43aa-a557-502c951296e8",
        organization_id=10,
        actor_id=1,
        filename="test.csv",
        csv_content=csv_data,
    )

    assert result["total"] == 2
    assert result["imported"] == 2
    assert result["updated"] == 0
    assert result["errors"] == []
    contact_domain_service.bulk_upsert.assert_called_once()
    import_log_repo.add.assert_called_once()


@pytest.mark.asyncio
async def test_import_contacts_missing_email_header():
    service = MagicMock()
    contact_list = ContactListEntity(
        id=1,
        uuid="50ce2993-12a2-43aa-a557-502c951296e8",
        organization_id=10,
        name="Test List",
    )
    service.get_by_uuid = AsyncMock(return_value=contact_list)
    contact_domain_service = MagicMock()
    import_log_repo = MagicMock()
    contact_activity_repo = MagicMock()

    usecase = ImportContactsUseCase(
        contact_list_domain_service=service,
        contact_domain_service=contact_domain_service,
        import_log_repo=import_log_repo,
        contact_activity_repo=contact_activity_repo,
    )

    csv_data = b"First_Name,Last_Name\nJohn,Doe\n"

    with pytest.raises(DomainError) as exc_info:
        await usecase.execute(
            list_uuid="50ce2993-12a2-43aa-a557-502c951296e8",
            organization_id=10,
            actor_id=1,
            filename="test.csv",
            csv_content=csv_data,
        )

    assert "email" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_import_contacts_rejects_empty_data_rows():
    service = MagicMock()
    contact_list = ContactListEntity(
        id=1,
        uuid="50ce2993-12a2-43aa-a557-502c951296e8",
        organization_id=10,
        name="Test List",
    )
    service.get_by_uuid = AsyncMock(return_value=contact_list)
    service.update_field_definitions = AsyncMock(return_value=contact_list)

    usecase = ImportContactsUseCase(
        contact_list_domain_service=service,
        contact_domain_service=MagicMock(),
        import_log_repo=MagicMock(),
        contact_activity_repo=MagicMock(),
    )

    with pytest.raises(DomainError) as exc_info:
        await usecase.execute(
            list_uuid=contact_list.uuid,
            organization_id=10,
            actor_id=1,
            filename="empty.csv",
            csv_content=b"Email,First_Name\n",
        )

    assert "no contact rows" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_import_contacts_reports_existing_and_in_file_duplicates():
    service = MagicMock()
    contact_list = ContactListEntity(
        id=1,
        uuid="50ce2993-12a2-43aa-a557-502c951296e8",
        organization_id=10,
        name="Test List",
        field_definitions=[],
    )
    service.get_by_uuid = AsyncMock(return_value=contact_list)
    service.update_field_definitions = AsyncMock(return_value=contact_list)

    existing_contact = ContactEntity(
        id=1, organization_id=10, contact_list_id=1, email="john@example.com"
    )
    contact_domain_service = MagicMock()
    contact_domain_service.get_existing_by_emails = AsyncMock(
        return_value=[existing_contact]
    )
    imported_contact = ContactEntity(
        id=2, organization_id=10, contact_list_id=1, email="jane@example.com"
    )
    contact_domain_service.bulk_upsert = AsyncMock(return_value=([imported_contact], 0))

    import_log_repo = MagicMock()
    import_log_repo.add = AsyncMock()
    contact_activity_repo = MagicMock()
    contact_activity_repo.add = AsyncMock()

    usecase = ImportContactsUseCase(
        contact_list_domain_service=service,
        contact_domain_service=contact_domain_service,
        import_log_repo=import_log_repo,
        contact_activity_repo=contact_activity_repo,
    )

    result = await usecase.execute(
        list_uuid=contact_list.uuid,
        organization_id=10,
        actor_id=1,
        filename="duplicates.csv",
        csv_content=(
            b"Email\n"
            b"john@example.com\n"
            b"john@example.com\n"
            b"jane@example.com\n"
        ),
    )

    assert result["imported"] == 1
    assert result["duplicates"] == 2
    assert result["skipped"] == 2
    assert result["reasons"]["duplicate_email"] == 2



@pytest.mark.asyncio
async def test_import_contacts_forbidden_org():
    service = MagicMock()
    contact_list = ContactListEntity(
        id=1,
        uuid="50ce2993-12a2-43aa-a557-502c951296e8",
        organization_id=99,
        name="Test List",
    )
    service.get_by_uuid = AsyncMock(return_value=contact_list)
    contact_domain_service = MagicMock()
    import_log_repo = MagicMock()
    contact_activity_repo = MagicMock()

    usecase = ImportContactsUseCase(
        contact_list_domain_service=service,
        contact_domain_service=contact_domain_service,
        import_log_repo=import_log_repo,
        contact_activity_repo=contact_activity_repo,
    )

    csv_data = b"Email\njohn@example.com\n"

    with pytest.raises(ForbiddenError):
        await usecase.execute(
            list_uuid="50ce2993-12a2-43aa-a557-502c951296e8",
            organization_id=10,
            actor_id=1,
            filename="test.csv",
            csv_content=csv_data,
        )
