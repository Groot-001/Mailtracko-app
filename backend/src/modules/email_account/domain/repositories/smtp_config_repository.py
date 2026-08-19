
from abc import ABC, abstractmethod

from src.modules.email_account.domain.entities.smtp_config_entity import SmtpConfigEntity


class ISmtpConfigRepository(ABC):

    @abstractmethod
    async def add(self, entity: SmtpConfigEntity) -> SmtpConfigEntity:
        pass

    @abstractmethod
    async def get_by_id(self, config_id: int) -> SmtpConfigEntity | None:
        pass

    @abstractmethod
    async def update(self, entity: SmtpConfigEntity) -> SmtpConfigEntity:
        pass

    @abstractmethod
    async def delete(self, config_id: int) -> None:
        pass