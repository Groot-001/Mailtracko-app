from abc import ABC, abstractmethod
from uuid import UUID


class CampaignSenderRepository(ABC):

    @abstractmethod
    async def create(
        self,
        sender,
    ):
        ...

    @abstractmethod
    async def update(
        self,
        sender,
    ):
        ...

    @abstractmethod
    async def delete(
        self,
        sender_id: UUID,
        organization_id: UUID,
    ) -> None:
        ...

    @abstractmethod
    async def list_by_campaign(
        self,
        campaign_id: UUID,
        organization_id: UUID,
    ):
        ...
