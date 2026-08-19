from abc import ABC, abstractmethod
from uuid import UUID


class CampaignSequenceRepository(ABC):

    @abstractmethod
    async def create(
        self,
        sequence,
    ):
        ...

    @abstractmethod
    async def update(
        self,
        sequence,
    ):
        ...

    @abstractmethod
    async def delete(
        self,
        sequence_id: UUID,
        organization_id: UUID,
    ) -> None:
        ...

    @abstractmethod
    async def get_by_campaign(
        self,
        campaign_id: UUID,
        organization_id: UUID,
    ):
        ...
