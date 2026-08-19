from typing import Any

from src.modules.auth.domain.entities.user_account_entity import UserAccountEntity
from src.modules.auth.domain.repositories.user_account_repository import IUserAccountRepository
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class UserAccountDomainService:
    """Domain service for user account entity operations."""

    def __init__(self, repository: IUserAccountRepository):
        self.repository = repository

    async def create_user_account(self, account_entity: UserAccountEntity) -> UserAccountEntity:
        """Persist a new user account."""
        try:
            return await self.repository.add(account_entity)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to create user account", internal_details=str(e)) from e

    async def get_user_account_by_user_id(
        self, user_id: int, type: str | None = None
    ) -> UserAccountEntity | None:
        """Retrieve an account by user ID, optionally filtered by type."""
        try:
            criteria: dict[str, Any] = {"user_id": user_id}
            if type:
                criteria["type"] = type
            return await self.repository.get_by(**criteria)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve user account", internal_details=str(e)) from e

    async def get_user_account_by_provider(
        self, provider: str, provider_account_id: str
    ) -> UserAccountEntity | None:
        """Retrieve an OAuth account by provider and external account ID."""
        try:
            return await self.repository.get_by(
                provider=provider, provider_account_id=provider_account_id
            )
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve OAuth account", internal_details=str(e)) from e

    async def update_user_account(self, account_entity: UserAccountEntity) -> UserAccountEntity:
        """Persist changes to an existing user account."""
        try:
            return await self.repository.update(account_entity)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to update user account", internal_details=str(e)) from e
