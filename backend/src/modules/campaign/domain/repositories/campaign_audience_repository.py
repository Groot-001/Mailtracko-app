from abc import ABC, abstractmethod
from uuid import UUID

from ..entities import CampaignAudience


class CampaignAudienceRepository(ABC):

    @abstractmethod
    async def create(
        self,
        audience: CampaignAudience,
    ) -> CampaignAudience:
        ...

    @abstractmethod
    async def update(
        self,
        audience: CampaignAudience,
    ) -> CampaignAudience:
        ...

    @abstractmethod
    async def delete(
        self,
        audience_id: UUID,
        organization_id: UUID,
    ) -> None:
        ...

    @abstractmethod
    async def list_by_campaign(
        self,
        campaign_id: UUID,
        organization_id: UUID,
    ) -> list[CampaignAudience]:
        ...
