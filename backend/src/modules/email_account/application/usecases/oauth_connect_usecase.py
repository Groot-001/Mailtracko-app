import json
import secrets

from src.modules.email_account.domain.services.email_account_domain_service import EmailAccountDomainService
from src.modules.email_account.infrastructure.oauth.google_mail_oauth_client import GoogleMailOAuthClient
from src.shared.exceptions.base_exceptions import DomainError, InvalidError, NotFoundError, ServerError
from src.shared.infrastructure.redis_client import get_redis


class OAuthConnectUseCase:

    def __init__(
        self,
        email_account_domain_service: EmailAccountDomainService,
        google_mail_oauth_client: GoogleMailOAuthClient,
    ):
        self.email_account_domain_service = email_account_domain_service
        self.google_mail_oauth_client = google_mail_oauth_client

    async def execute(self, provider: str, organization_id: int, actor_id: int, account_uuid: str | None = None) -> str:
        try:
            state = secrets.token_urlsafe(32)
            redis = await get_redis()

            state_data = {"provider": provider, "organization_id": organization_id, "actor_id": actor_id, "email": None}
            if account_uuid:
                account = await self.email_account_domain_service.get_account_by_uuid(account_uuid)
                if not account or account.organization_id != organization_id:
                    raise NotFoundError(error="Email account not found")
                state_data["email"] = account.email

            await redis.setex(f"email_oauth_state:{state}", 300, json.dumps(state_data))

            if provider != "gmail":
                raise InvalidError(error=f"Unsupported OAuth provider: {provider}")
            return self.google_mail_oauth_client.get_authorization_url(state=state)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to initiate OAuth connection", internal_details=str(e)) from e
