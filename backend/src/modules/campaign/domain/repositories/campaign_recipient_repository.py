from abc import ABC, abstractmethod
from uuid import UUID


class CampaignRecipientRepository(ABC):
    """Repository interface for campaign recipients."""

    @abstractmethod
    async def create(
        self,
        recipient,
    ):
        ...

    @abstractmethod
    async def update(
        self,
        recipient,
    ):
        ...

    @abstractmethod
    async def get_by_campaign(
        self,
        campaign_id: UUID,
        organization_id: UUID,
    ):
        ...

    @abstractmethod
    async def delete(
        self,
        recipient_id: UUID,
        organization_id: UUID,
    ) -> None:
        ...
