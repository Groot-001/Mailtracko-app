from abc import abstractmethod

from src.modules.organization.domain.entities.organization_invitation_entity import (
    OrganizationInvitationEntity,
)
from src.shared.domain.repository.base_repository_interface import IBaseRepository


class IOrganizationInvitationRepository(IBaseRepository[OrganizationInvitationEntity]):
    """
    Interface for the organization invitation repository.
    """

    @abstractmethod
    async def get_by_token_hash(
        self,
        token_hash: str,
    ) -> OrganizationInvitationEntity | None:
        """
        Retrieves invitation by hashed invitation token.
        """
        pass

    @abstractmethod
    async def get_pending_by_email(
        self,
        *,
        organization_id: int,
        email: str,
    ) -> OrganizationInvitationEntity | None:
        """
        Retrieves pending invitation by organization ID and email.
        """
        pass

    @abstractmethod
    async def get_pending_by_email_global(
        self,
        email: str,
    ) -> list[OrganizationInvitationEntity]:
        """
        Retrieves all pending invitations by email across all organizations.
        Used during onboarding to detect pending invitations before org creation.
        """
        pass

    @abstractmethod
    async def list_paginated(
        self,
        *,
        organization_id: int,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[OrganizationInvitationEntity], int]:
        """
        Lists organization invitations, optionally filtered by status.
        Returns the slice plus the total count for pagination metadata.
        """
        pass