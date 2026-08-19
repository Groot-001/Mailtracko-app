from src.modules.contacts.infrastructure.oauth.google_sheets_oauth_client import (
    GoogleSheetsOAuthClient,
)
from src.modules.email_account.domain.repositories.oauth_config_repository import (
    IOauthConfigRepository,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    InvalidError,
    NotFoundError,
    ServerError,
)
from src.shared.infrastructure.encryption.fernet_encryption import decrypt


class ListSheetTabsUseCase:
    """List all tabs in a Google Sheet."""

    def __init__(
        self,
        google_sheets_oauth_client: GoogleSheetsOAuthClient,
        oauth_config_repo: IOauthConfigRepository,
    ):
        self.google_sheets_oauth_client = google_sheets_oauth_client
        self.oauth_config_repo = oauth_config_repo

    async def execute(self, sheet_url: str, organization_id: int) -> list[dict]:
        try:
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
            metadata = await self.google_sheets_oauth_client.get_sheet_metadata(
                access_token, spreadsheet_id
            )

            tabs = []
            for sheet in metadata.get("sheets", []):
                props = sheet.get("properties", {})
                tabs.append(
                    {
                        "title": props.get("title", ""),
                        "sheet_id": props.get("sheetId", 0),
                        "row_count": props.get("gridProperties", {}).get("rowCount", 0),
                    }
                )

            if not tabs:
                raise InvalidError(error="The Google Sheet does not contain any tabs to import.")
            return tabs

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to list sheet tabs", internal_details=str(e)
            ) from e
