
from src.modules.email_account.domain.entities.email_account_entity import EmailAccountEntity
from src.modules.email_account.domain.entities.smtp_config_entity import SmtpConfigEntity
from src.modules.email_account.domain.entities.oauth_config_entity import OauthConfigEntity
from src.modules.email_account.domain.repositories.email_account_repository import IEmailAccountRepository
from src.modules.email_account.domain.repositories.smtp_config_repository import ISmtpConfigRepository
from src.modules.email_account.domain.repositories.oauth_config_repository import IOauthConfigRepository
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class EmailAccountDomainService:

    def __init__(
        self,
        account_repository: IEmailAccountRepository,
        smtp_config_repository: ISmtpConfigRepository,
        oauth_config_repository: IOauthConfigRepository,
    ):
        self.account_repository = account_repository
        self.smtp_config_repository = smtp_config_repository
        self.oauth_config_repository = oauth_config_repository

    # ---- Account operations ----

    async def create_account(self, entity: EmailAccountEntity) -> EmailAccountEntity:
        try:
            return await self.account_repository.add(entity)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to create email account", internal_details=str(e)) from e

    async def get_account_by_id(self, account_id: int) -> EmailAccountEntity | None:
        try:
            return await self.account_repository.get_by(id=account_id, deleted_at=None)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve email account", internal_details=str(e)) from e

    async def get_account_by_uuid(self, uuid: str) -> EmailAccountEntity | None:
        try:
            return await self.account_repository.get_by(uuid=uuid, deleted_at=None)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve email account", internal_details=str(e)) from e

    async def update_account(self, entity: EmailAccountEntity) -> EmailAccountEntity:
        try:
            return await self.account_repository.update(entity)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to update email account", internal_details=str(e)) from e

    async def get_by_email_and_organization(
        self, email: str, organization_id: int,
    ) -> EmailAccountEntity | None:
        try:
            return await self.account_repository.get_by_email_and_organization(email, organization_id)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve email account", internal_details=str(e)) from e

    async def get_by_email_and_organization_including_deleted(
        self, email: str, organization_id: int,
    ) -> EmailAccountEntity | None:
        try:
            return await self.account_repository.get_by_email_and_organization_including_deleted(
                email, organization_id
            )
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve email account", internal_details=str(e)) from e

    async def list_by_organization(
        self, organization_id: int, limit: int = 50, offset: int = 0,
    ) -> tuple[list[EmailAccountEntity], int]:
        try:
            return await self.account_repository.list_by_organization(organization_id, limit, offset)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to list email accounts", internal_details=str(e)) from e

    async def list_active_by_organization(self, organization_id: int) -> list[EmailAccountEntity]:
        try:
            return await self.account_repository.list_active_by_organization(organization_id)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to list active email accounts", internal_details=str(e)) from e

    async def list_expired_pending(self, expiry_minutes: int = 1440) -> list[EmailAccountEntity]:
        try:
            return await self.account_repository.list_expired_pending(expiry_minutes)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to list expired pending accounts", internal_details=str(e)) from e

    async def count_by_organization(self, organization_id: int) -> int:
        try:
            return await self.account_repository.count_by_organization(organization_id)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to count email accounts", internal_details=str(e)) from e

    # ---- SMTP config operations ----

    async def create_smtp_config(self, entity: SmtpConfigEntity) -> SmtpConfigEntity:
        try:
            return await self.smtp_config_repository.add(entity)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to create SMTP config", internal_details=str(e)) from e

    async def get_smtp_config(self, config_id: int) -> SmtpConfigEntity | None:
        try:
            return await self.smtp_config_repository.get_by_id(config_id)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve SMTP config", internal_details=str(e)) from e

    async def update_smtp_config(self, entity: SmtpConfigEntity) -> SmtpConfigEntity:
        try:
            return await self.smtp_config_repository.update(entity)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to update SMTP config", internal_details=str(e)) from e

    async def delete_smtp_config(self, config_id: int) -> None:
        try:
            await self.smtp_config_repository.delete(config_id)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to delete SMTP config", internal_details=str(e)) from e

    # ---- OAuth config operations ----

    async def create_oauth_config(self, entity: OauthConfigEntity) -> OauthConfigEntity:
        try:
            return await self.oauth_config_repository.add(entity)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to create OAuth config", internal_details=str(e)) from e

    async def get_oauth_config(self, config_id: int) -> OauthConfigEntity | None:
        try:
            return await self.oauth_config_repository.get_by_id(config_id)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve OAuth config", internal_details=str(e)) from e

    async def update_oauth_config(self, entity: OauthConfigEntity) -> OauthConfigEntity:
        try:
            return await self.oauth_config_repository.update(entity)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to update OAuth config", internal_details=str(e)) from e

    async def delete_oauth_config(self, config_id: int) -> None:
        try:
            await self.oauth_config_repository.delete(config_id)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to delete OAuth config", internal_details=str(e)) from e