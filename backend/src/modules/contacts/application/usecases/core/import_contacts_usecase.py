from src.modules.contacts.application.usecases.core.csv_utils import (
    decode_csv,
    parse_rows,
)
from src.modules.contacts.domain.entities.contact_activity_entity import (
    ContactActivityEntity,
)
from src.modules.contacts.domain.entities.contact_entity import ContactEntity
from src.modules.contacts.domain.entities.contact_import_log_entity import (
    ContactImportLogEntity,
)
from src.modules.contacts.domain.enums.contact_enums import (
    ContactActivityTypeEnum,
    ImportStatusEnum,
)
from src.modules.contacts.domain.repositories.contact_activity_repository import (
    IContactActivityRepository,
)
from src.modules.contacts.domain.repositories.contact_import_log_repository import (
    IContactImportLogRepository,
)
from src.modules.contacts.domain.services.contact_domain_service import (
    ContactDomainService,
)
from src.modules.contacts.domain.services.contact_list_domain_service import (
    ContactListDomainService,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ForbiddenError,
    InvalidError,
    NotFoundError,
    ServerError,
)


class ImportContactsUseCase:
    """Use case for CSV import — parse, persist, log activities."""

    def __init__(
        self,
        contact_list_domain_service: ContactListDomainService,
        contact_domain_service: ContactDomainService,
        import_log_repo: IContactImportLogRepository,
        contact_activity_repo: IContactActivityRepository,
    ):
        self.contact_list_domain_service = contact_list_domain_service
        self.contact_domain_service = contact_domain_service
        self.import_log_repo = import_log_repo
        self.contact_activity_repo = contact_activity_repo

    async def execute(
        self,
        list_uuid: str,
        organization_id: int,
        actor_id: int,
        filename: str,
        csv_content: bytes,
    ) -> dict:
        try:
            existing = await self.contact_list_domain_service.get_by_uuid(list_uuid)
            if existing.organization_id != organization_id:
                raise ForbiddenError(
                    error="You do not have access to this contact list"
                )
            if existing.id is None:
                raise NotFoundError(error="Contact list not found")

            content_str = decode_csv(csv_content)
            parsed_rows, error_rows, header_mapping, extra_fields = parse_rows(
                content_str
            )

            if extra_fields:
                existing = (
                    await self.contact_list_domain_service.update_field_definitions(
                        existing,
                        extra_fields,
                    )
                )

            if not parsed_rows:
                if error_rows:
                    raise InvalidError(
                        error="No valid contacts were found in the CSV file",
                        errors={"rows": error_rows[:50]},
                    )
                raise InvalidError(error="The CSV file contains no contact rows")

            # Import is intentionally insert-only. Existing contacts and
            # repeated emails in the same file are reported as duplicates
            # instead of silently updating existing records.
            seen_emails: set[str] = set()
            unique_rows: list[dict] = []
            duplicate_count = 0
            for row in parsed_rows:
                email = row["email"]
                if email in seen_emails:
                    duplicate_count += 1
                    continue
                seen_emails.add(email)
                unique_rows.append(row)

            existing_contacts = await self.contact_domain_service.get_existing_by_emails(
                list(seen_emails),
                existing.id,
            )
            existing_emails = {contact.email for contact in existing_contacts}
            duplicate_count += sum(
                1 for row in unique_rows if row["email"] in existing_emails
            )
            import_rows = [
                row for row in unique_rows if row["email"] not in existing_emails
            ]

            entities = [
                ContactEntity(
                    organization_id=organization_id,
                    contact_list_id=existing.id,
                    email=r["email"],
                    metadata=r["metadata_dict"],
                )
                for r in import_rows
            ]

            all_contacts, _ = await self.contact_domain_service.bulk_upsert(entities)
            imported_count = len(all_contacts)
            updated_count = 0

            for c in all_contacts:
                activity_type = ContactActivityTypeEnum.IMPORTED.value
                activity = ContactActivityEntity(
                    contact_id=c.id,
                    organization_id=organization_id,
                    activity_type=activity_type,
                    description=f"Contact imported via {filename}",
                    metadata={"filename": filename},
                )
                await self.contact_activity_repo.add(activity)

            log = ContactImportLogEntity(
                organization_id=organization_id,
                contact_list_id=existing.id,
                filename=filename,
                column_mapping=header_mapping,
                total_rows=len(parsed_rows) + len(error_rows),
                success_count=len(all_contacts),
                error_count=len(error_rows),
                errors=error_rows or None,
                status=ImportStatusEnum.COMPLETED.value,
                created_by_id=actor_id,
            )
            await self.import_log_repo.add(log)

            return {
                "total": len(parsed_rows) + len(error_rows),
                "imported": imported_count,
                "updated": updated_count,
                "errors": error_rows,
                "duplicates": duplicate_count,
                "skipped": duplicate_count + len(error_rows),
                "reasons": {
                    "duplicate_email": duplicate_count,
                    "invalid_row": len(error_rows),
                },
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while importing contacts",
                internal_details=str(e),
            ) from e
