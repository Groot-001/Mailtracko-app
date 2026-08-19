from src.modules.email_account.domain.events.email_account_domain_events import EmailAccountDisconnectedEvent
from src.modules.email_account.domain.services.email_account_domain_service import EmailAccountDomainService
from src.shared.exceptions.base_exceptions import DomainError, NotFoundError, ServerError
from src.shared.mediator.mediator import mediator


class ListAccountsUseCase:
    def __init__(self, email_account_domain_service: EmailAccountDomainService):
        self.email_account_domain_service = email_account_domain_service

    async def execute(
        self,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list, int]:
        try:
            return await self.email_account_domain_service.list_by_organization(
                organization_id, limit, offset
            )
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to list email accounts", internal_details=str(e)) from e


class GetAccountUseCase:
    def __init__(self, email_account_domain_service: EmailAccountDomainService):
        self.email_account_domain_service = email_account_domain_service

    async def execute(self, account_uuid: str, organization_id: int) -> dict:
        try:
            account = await self.email_account_domain_service.get_account_by_uuid(account_uuid)
            if not account or account.organization_id != organization_id:
                raise NotFoundError(error="Email account not found")
            return {
                "uuid": account.uuid,
                "organization_id": account.organization_id,
                "email": account.email,
                "provider": account.provider,
                "sender_name": account.sender_name,
                "status": account.status,
                "health_status": account.health_status,
                "health_score": account.health_score,
                "health_details": account.health_details,
                "daily_sent_count": account.daily_sent_count,
                "last_sent_date": account.last_sent_date,
                "sending_limit": account.sending_limit,
                "reply_to": account.reply_to,
                "signature": account.signature,
                "last_used_at": account.last_used_at,
                "created_at": account.created_at,
            }
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve email account", internal_details=str(e)) from e

class UpdateAccountUseCase:
    def __init__(self, email_account_domain_service: EmailAccountDomainService):
        self.email_account_domain_service = email_account_domain_service

    async def execute(
        self,
        account_uuid: str,
        organization_id: int,
        sender_name: str | None = None,
        sending_limit: int | None = None,
        reply_to: str | None = None,
        signature: str | None = None,
        actor_id: int | None = None,
    ) -> dict:
        try:
            account = await self.email_account_domain_service.get_account_by_uuid(account_uuid)
            if not account or account.organization_id != organization_id:
                raise NotFoundError(error="Email account not found")

            if sender_name is not None:
                account.sender_name = sender_name
            if sending_limit is not None:
                account.sending_limit = sending_limit
            if reply_to is not None:
                account.reply_to = reply_to
            if signature is not None:
                account.signature = signature
            if actor_id is not None:
                account.updated_by_id = actor_id

            account.mark_updated()
            updated = await self.email_account_domain_service.update_account(account)

            return {
                "uuid": updated.uuid,
                "organization_id": updated.organization_id,
                "email": updated.email,
                "provider": updated.provider,
                "sender_name": updated.sender_name,
                "status": updated.status,
                "health_status": updated.health_status,
                "health_score": updated.health_score,
                "health_details": updated.health_details,
                "sending_limit": updated.sending_limit,
                "reply_to": updated.reply_to,
                "signature": updated.signature,
                "last_used_at": updated.last_used_at,
            }
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to update email account", internal_details=str(e)) from e


class DisconnectAccountUseCase:
    def __init__(self, email_account_domain_service: EmailAccountDomainService):
        self.email_account_domain_service = email_account_domain_service

    async def execute(self, account_uuid: str, organization_id: int, actor_id: int) -> dict:
        try:
            account = await self.email_account_domain_service.get_account_by_uuid(account_uuid)
            if not account or account.organization_id != organization_id:
                raise NotFoundError(error="Email account not found")

            account.mark_disconnected()
            account.soft_delete()
            account.updated_by_id = actor_id
            await self.email_account_domain_service.update_account(account)

            if account.smtp_config_id:
                await self.email_account_domain_service.delete_smtp_config(account.smtp_config_id)
            if account.oauth_config_id:
                await self.email_account_domain_service.delete_oauth_config(account.oauth_config_id)

            account.add_event(
                EmailAccountDisconnectedEvent(
                    account_id=account.id,
                    account_uuid=account.uuid,
                    organization_id=organization_id,
                    email=account.email,
                )
            )
            for event in account.pull_events():
                await mediator.publish(event)

            return {"message": "Email account disconnected successfully"}
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to disconnect email account", internal_details=str(e)) from e