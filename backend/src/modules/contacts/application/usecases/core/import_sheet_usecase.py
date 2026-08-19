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
from src.modules.contacts.infrastructure.oauth.google_sheets_oauth_client import (
    GoogleSheetsOAuthClient,
)
from src.modules.contacts.application.usecases.core.csv_utils import (
    _EMAIL_RE,
    normalize_import_header,
)
from src.modules.email_account.domain.repositories.oauth_config_repository import (
    IOauthConfigRepository,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ForbiddenError,
    InvalidError,
    NotFoundError,
    ServerError,
)
from src.shared.infrastructure.encryption.fernet_encryption import decrypt


class ImportSheetUseCase:
    """Import contacts from a Google Sheet tab."""

    def __init__(
        self,
        contact_list_domain_service: ContactListDomainService,
        contact_domain_service: ContactDomainService,
        import_log_repo: IContactImportLogRepository,
        google_sheets_oauth_client: GoogleSheetsOAuthClient,
        oauth_config_repo: IOauthConfigRepository,
        contact_activity_repo: IContactActivityRepository,
    ):
        self.contact_list_domain_service = contact_list_domain_service
        self.contact_domain_service = contact_domain_service
        self.import_log_repo = import_log_repo
        self.google_sheets_oauth_client = google_sheets_oauth_client
        self.oauth_config_repo = oauth_config_repo
        self.contact_activity_repo = contact_activity_repo

    async def execute(
        self,
        list_uuid: str,
        organization_id: int,
        actor_id: int,
        sheet_url: str,
        tab: str,
    ) -> dict:
        try:
            existing = await self.contact_list_domain_service.get_by_uuid(list_uuid)
            if existing.organization_id != organization_id:
                raise ForbiddenError(
                    error="You do not have access to this contact list"
                )
            if existing.id is None:
                raise NotFoundError(error="Contact list not found")

            config = await self.oauth_config_repo.get_by_context(
                organization_id, "google_sheets"
            )
            if not config:
                raise NotFoundError(
                    error=(
                        "Google Sheets is not connected for this workspace. "
                        "Please connect your Google account first."
                    )
                )

            refresh_token = decrypt(config.encrypted_refresh_token)
            tokens = await self.google_sheets_oauth_client.refresh_access_token(
                refresh_token
            )
            access_token = tokens["access_token"]

            spreadsheet_id = self.google_sheets_oauth_client.extract_sheet_id_from_url(
                sheet_url
            )
            values = await self.google_sheets_oauth_client.get_sheet_data(
                access_token, spreadsheet_id, tab
            )

            if not values or len(values) < 2:
                raise InvalidError(error="The selected Google Sheet contains no contact rows")

            raw_headers = [str(h or "").strip() for h in values[0]]
            headers: list[str] = []
            used_headers: dict[str, int] = {}
            for raw_header in raw_headers:
                normalized = normalize_import_header(raw_header)
                occurrence = used_headers.get(normalized, 0) + 1
                used_headers[normalized] = occurrence
                headers.append(
                    normalized if occurrence == 1 else f"{normalized}_{occurrence}"
                )

            email_col_idx = next(
                (i for i, h in enumerate(headers) if h == "email"), None
            )
            if email_col_idx is None:
                raise DomainError(error="Sheet must contain an 'email' column")

            extra_field_names = [h for i, h in enumerate(headers) if h != "email"]

            if extra_field_names:
                existing = (
                    await self.contact_list_domain_service.update_field_definitions(
                        existing,
                        extra_field_names,
                    )
                )

            parsed_rows = []
            error_rows = []
            for row_idx, row in enumerate(values[1:], start=2):
                email_val = ""
                metadata = {}
                for col_idx, cell in enumerate(row):
                    if col_idx >= len(headers):
                        break
                    val = (cell or "").strip()
                    if col_idx == email_col_idx:
                        email_val = val.lower()
                    else:
                        if val:
                            metadata[headers[col_idx]] = val

                if not email_val:
                    error_rows.append({"row": row_idx, "error": "Missing email"})
                    continue

                if not _EMAIL_RE.match(email_val):
                    error_rows.append(
                        {
                            "row": row_idx,
                            "error": f"Invalid email format: {email_val}",
                        }
                    )
                    continue

                parsed_rows.append(
                    {
                        "email": email_val,
                        "metadata_dict": metadata or None,
                    }
                )

            if not parsed_rows:
                raise InvalidError(
                    error="No valid contacts were found in the selected Google Sheet",
                    errors={"rows": error_rows[:50]},
                )

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
                activity = ContactActivityEntity(
                    contact_id=c.id,
                    organization_id=organization_id,
                    activity_type=ContactActivityTypeEnum.IMPORTED.value,
                    description=f"Contact imported from Google Sheets ({tab})",
                    metadata={"sheet_url": sheet_url, "tab": tab},
                )
                await self.contact_activity_repo.add(activity)

            log = ContactImportLogEntity(
                organization_id=organization_id,
                contact_list_id=existing.id,
                filename=f"sheets-{tab}.csv",
                column_mapping={
                    raw_headers[i] or f"Column {i + 1}": headers[i]
                    for i in range(len(headers))
                },
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
                error="An error occurred while importing from Google Sheets",
                internal_details=str(e),
            ) from e
