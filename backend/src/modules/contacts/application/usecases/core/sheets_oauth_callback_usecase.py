from src.modules.contacts.infrastructure.oauth.google_sheets_oauth_client import (
    GoogleSheetsOAuthClient,
)
from src.modules.email_account.domain.entities.oauth_config_entity import (
    OauthConfigEntity,
)
from src.modules.email_account.domain.repositories.oauth_config_repository import (
    IOauthConfigRepository,
)
from src.shared.exceptions.base_exceptions import DomainError, InvalidError, ServerError
from src.shared.infrastructure.encryption.fernet_encryption import encrypt
from src.shared.security.oauth_state import parse_oauth_state


class SheetsOAuthCallbackUseCase:
    """Handle Google Sheets OAuth callback — exchange code, store token."""

    def __init__(
        self,
        google_sheets_oauth_client: GoogleSheetsOAuthClient,
        oauth_config_repo: IOauthConfigRepository,
    ):
        self.google_sheets_oauth_client = google_sheets_oauth_client
        self.oauth_config_repo = oauth_config_repo

    async def execute(self, code: str, state: str) -> str:
        try:
            state_data = parse_oauth_state(state, "google-sheets")
            organization_id = int(state_data["organization_id"])
            organization_uuid = state_data.get(
                "organization_uuid", str(organization_id)
            )

            tokens = await self.google_sheets_oauth_client.exchange_code(code)
            refresh_token = tokens.get("refresh_token")
            if not refresh_token:
                raise InvalidError(
                    error="No refresh token returned. Please re-authorize."
                )

            existing = await self.oauth_config_repo.get_by_context(
                organization_id, "google_sheets"
            )
            if existing:
                existing.encrypted_refresh_token = encrypt(refresh_token)
                await self.oauth_config_repo.update(existing)
            else:
                config = OauthConfigEntity(
                    encrypted_refresh_token=encrypt(refresh_token),
                    organization_id=organization_id,
                    purpose="google_sheets",
                )
                await self.oauth_config_repo.add(config)

            return f"Sheets connected successfully for organization {organization_uuid}"

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Sheets OAuth callback failed", internal_details=str(e)
            ) from e
