
from abc import ABC, abstractmethod

from src.modules.email_account.domain.entities.oauth_config_entity import OauthConfigEntity


class IOauthConfigRepository(ABC):

    @abstractmethod
    async def add(self, entity: OauthConfigEntity) -> OauthConfigEntity:
        pass

    @abstractmethod
    async def get_by_id(self, config_id: int) -> OauthConfigEntity | None:
        pass

    @abstractmethod
    async def get_by_context(self, organization_id: int, purpose: str) -> OauthConfigEntity | None:
        pass

    @abstractmethod
    async def update(self, entity: OauthConfigEntity) -> OauthConfigEntity:
        pass

    @abstractmethod
    async def delete(self, config_id: int) -> None:
        pass