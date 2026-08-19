# Keep the domain service independent from deployment and data-loading scripts.
from src.modules.organization.domain.entities.organization_entity import (
    OrganizationEntity,
)
from src.modules.organization.domain.enums.organization_enums import (
    OrganizationStatusEnum,
)
from src.modules.organization.domain.repositories.organization_repository import (
    IOrganizationRepository,
)
from src.shared.exceptions.base_exceptions import (
    ConflictError,
    CreateError,
    DomainError,
    InvalidError,
    ServerError,
    UpdateError,
)


class OrganizationDomainService:
    """
    Service class for organization domain logic.
    """

    def __init__(self, repository: IOrganizationRepository):
        self.repository = repository

    async def create_organization(
        self,
        organization_entity: OrganizationEntity,
    ) -> OrganizationEntity:
        """
        Creates a new organization/workspace.

        Normal signup users create an organization during onboarding and become
        the owner through organization_members.
        """
        try:
            await self._ensure_owner_has_no_active_organization(
                owner_id=organization_entity.owner_id,
            )

            return await self.repository.add(organization_entity)

        except DomainError:
            raise
        except Exception as e:
            raise CreateError(
                error="Failed to create organization",
                internal_details=str(e),
            ) from e

    async def activate_organization(
        self,
        organization_id: int,
    ) -> OrganizationEntity:
        """
        Activates organization.

        Kept for compatibility, although organizations are active by default now.
        """
        try:
            organization = await self.repository.get_by(
                id=organization_id,
                deleted_at=None,
            )

            if not organization or not organization.id:
                raise InvalidError(error="Organization not found")

            organization.status = OrganizationStatusEnum.ACTIVE.value
            organization.mark_updated()

            return await self.repository.update(organization)

        except DomainError:
            raise
        except Exception as e:
            raise UpdateError(
                error="Failed to activate organization",
                internal_details=str(e),
            ) from e

    async def request_organization_deletion(
        self,
        organization_id: int,
        actor_id: int,
        grace_period_days: int = 3,
    ) -> OrganizationEntity:
        """
        Schedules or reschedules organization deletion after grace period.
        """
        try:
            organization = await self.repository.get_by(
                id=organization_id,
                deleted_at=None,
            )

            if not organization or not organization.id:
                raise InvalidError(error="Organization not found")

            if organization.scheduled_deletion_at is not None:
                 return organization
             
            organization.request_deletion(
                requested_by_id=actor_id,
                grace_period_days=grace_period_days,
            )
            organization.updated_by_id = actor_id

            return await self.repository.update(organization)

        except DomainError:
            raise
        except Exception as e:
            raise UpdateError(
                error="Failed to request organization deletion",
                internal_details=str(e),
            ) from e

    async def update_organization(
        self,
        organization_entity: OrganizationEntity,
        actor_id: int,
    ) -> OrganizationEntity:
        """
        Updates organization details/profile.
        """
        try:
            organization_entity.updated_by_id = actor_id
            organization_entity.mark_updated()

            return await self.repository.update(organization_entity)

        except DomainError:
            raise
        except Exception as e:
            raise UpdateError(
                error="Failed to update organization",
                internal_details=str(e),
            ) from e

    async def get_organization_by_id(
        self,
        organization_id: int,
    ) -> OrganizationEntity | None:
        """
        Retrieves organization by ID.
        """
        try:
            return await self.repository.get_by(id=organization_id, deleted_at=None)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to retrieve organization",
                internal_details=str(e),
            ) from e

    async def get_organization_by_uuid(
        self,
        uuid: str,
    ) -> OrganizationEntity | None:
        """
        Retrieves organization by UUID.
        """
        try:
            return await self.repository.get_by(uuid=uuid, deleted_at=None)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to retrieve organization",
                internal_details=str(e),
            ) from e

    async def get_active_organization_by_owner_id(
        self,
        owner_id: int,
    ) -> OrganizationEntity | None:
        """
        Retrieves active organization owned by user.
        """
        try:
            return await self.repository.get_active_by_owner_id(owner_id=owner_id)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to retrieve active organization",
                internal_details=str(e),
            ) from e

    async def _ensure_owner_has_no_active_organization(
        self,
        *,
        owner_id: int,
    ) -> None:
        """
        Ensures owner is not creating another active organization.
        """
        try:
            existing_organization = await self.repository.get_active_by_owner_id(
                owner_id=owner_id,
            )

            if existing_organization:
                raise ConflictError(
                    error="User already owns an active organization"
                )
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to verify organization ownership",
                internal_details=str(e),
            ) from e
