from datetime import UTC, datetime

from src.modules.email_account.domain.events.email_account_domain_events import EmailAccountVerifiedEvent
from src.modules.email_account.domain.services.email_account_domain_service import EmailAccountDomainService
from src.shared.exceptions.base_exceptions import DomainError, InvalidError, NotFoundError, ServerError
from src.shared.infrastructure.hasher.hasher import HasherService
from src.shared.mediator.mediator import mediator


class SmtpVerifyUseCase:

    def __init__(
        self,
        email_account_domain_service: EmailAccountDomainService,
        hasher_service: HasherService,
    ):
        self.email_account_domain_service = email_account_domain_service
        self.hasher_service = hasher_service

    async def execute(
        self,
        account_uuid: str,
        code: str,
        organization_id: int,
        actor_id: int,
    ) -> dict:
        try:
            account = await self.email_account_domain_service.get_account_by_uuid(account_uuid)
            if not account or account.organization_id != organization_id:
                raise NotFoundError(error="Email account not found")

            if not account.is_pending_verification():
                raise InvalidError(error="Email account is not pending verification")

            smtp_config = await self.email_account_domain_service.get_smtp_config(account.smtp_config_id)
            if not smtp_config:
                raise ServerError(error="SMTP configuration not found")

            if smtp_config.code_expires_at and datetime.now(UTC) > smtp_config.code_expires_at:
                raise InvalidError(error="Verification code has expired. Request a new one.")

            if not self.hasher_service.verify_deterministic_hash(code, smtp_config.verification_code_hash):
                raise InvalidError(error="Invalid verification code")

            account.mark_active()
            account.updated_by_id = actor_id
            await self.email_account_domain_service.update_account(account)

            smtp_config.verification_code_hash = None
            smtp_config.code_expires_at = None
            smtp_config.mark_updated()
            await self.email_account_domain_service.update_smtp_config(smtp_config)

            account.add_event(
                EmailAccountVerifiedEvent(
                    account_id=account.id,
                    account_uuid=account.uuid,
                    organization_id=account.organization_id,
                    email=account.email,
                )
            )
            for event in account.pull_events():
                await mediator.publish(event)

            return {
                "uuid": account.uuid,
                "email": account.email,
                "provider": account.provider,
                "status": account.status,
            }
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to verify email account", internal_details=str(e)) from e
