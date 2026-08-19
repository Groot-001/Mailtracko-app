from src.modules.contacts.infrastructure.oauth.google_sheets_oauth_client import (
    GoogleSheetsOAuthClient,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError
from src.shared.security.oauth_state import create_oauth_state


class InitiateSheetsOAuthUseCase:
    """Initiate Google Sheets OAuth flow — returns authorization URL."""

    def __init__(self, google_sheets_oauth_client: GoogleSheetsOAuthClient):
        self.google_sheets_oauth_client = google_sheets_oauth_client

    async def execute(
        self, organization_id: int, organization_uuid: str, actor_id: int
    ) -> str:
        try:
            state = create_oauth_state(
                "google-sheets",
                organization_id=organization_id,
                organization_uuid=organization_uuid,
                actor_id=actor_id,
            )
            return self.google_sheets_oauth_client.get_authorization_url(state=state)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to initiate Sheets OAuth", internal_details=str(e)
            ) from e
