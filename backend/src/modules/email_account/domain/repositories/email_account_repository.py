from abc import ABC, abstractmethod

from src.modules.email_account.domain.entities.email_account_entity import EmailAccountEntity


class IEmailAccountRepository(ABC):

    @abstractmethod
    async def add(self, entity: EmailAccountEntity) -> EmailAccountEntity:
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: int) -> EmailAccountEntity | None:
        pass

    @abstractmethod
    async def get_by_uuid(self, uuid: str) -> EmailAccountEntity | None:
        pass

    @abstractmethod
    async def get_by(self, **kwargs) -> EmailAccountEntity | None:
        pass

    @abstractmethod
    async def update(self, entity: EmailAccountEntity) -> EmailAccountEntity:
        pass

    @abstractmethod
    async def delete(self, entity_id: int) -> None:
        pass

    @abstractmethod
    async def list_by_organization(
        self, organization_id: int, limit: int = 50, offset: int = 0,
    ) -> tuple[list[EmailAccountEntity], int]:
        pass

    @abstractmethod
    async def get_by_email_and_organization(
        self, email: str, organization_id: int,
    ) -> EmailAccountEntity | None:
        pass

    @abstractmethod
    async def get_by_email_and_organization_including_deleted(
        self, email: str, organization_id: int,
    ) -> EmailAccountEntity | None:
        pass

    @abstractmethod
    async def list_active_by_organization(
        self, organization_id: int,
    ) -> list[EmailAccountEntity]:
        pass

    @abstractmethod
    async def list_expired_pending(
        self, expiry_minutes: int = 1440,
    ) -> list[EmailAccountEntity]:
        pass

    @abstractmethod
    async def count_by_organization(self, organization_id: int) -> int:
        pass