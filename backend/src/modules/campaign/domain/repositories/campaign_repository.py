from abc import ABC, abstractmethod
from uuid import UUID

from ..entities import Campaign


class CampaignRepository(ABC):
    """Repository interface for Campaign aggregate."""

    @abstractmethod
    async def create(
        self,
        campaign: Campaign,
    ) -> Campaign:
        """Persist a new campaign."""

    @abstractmethod
    async def update(
        self,
        campaign: Campaign,
    ) -> Campaign:
        """Persist campaign changes."""

    @abstractmethod
    async def delete(
        self,
        campaign_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Delete a campaign."""

    @abstractmethod
    async def get_by_id(
        self,
        campaign_id: UUID,
        organization_id: UUID,
    ) -> Campaign | None:
        """Return campaign by id."""

    @abstractmethod
    async def exists(
        self,
        campaign_id: UUID,
        organization_id: UUID,
    ) -> bool:
        """Return whether the campaign exists."""

    @abstractmethod
    async def list_by_organization(
        self,
        organization_id: UUID,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Campaign]:
        """Return campaigns for an organization."""
