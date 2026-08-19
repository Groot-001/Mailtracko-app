from src.modules.organization.domain.entities.organization_entity import (
    OrganizationEntity,
)
from src.modules.organization.domain.services.organization_domain_service import (
    OrganizationDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class GetOrganizationDetailsUseCase:
    """
    Use case for getting organization details.
    """

    def __init__(
        self,
        organization_domain_service: OrganizationDomainService,
    ):
        self.organization_domain_service = organization_domain_service

    async def execute(self, organization_id: int) -> OrganizationEntity:
        """
        Executes the use case to get organization details.
        """
        try:
            organization = (
                await self.organization_domain_service.get_organization_by_id(
                    organization_id
                )
            )

            if not organization or not organization.id:
                raise ServerError(
                    error="Error while retrieving organization details",
                    internal_details=f"No organization found with id {organization_id}",
                )

            return organization

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while retrieving organization details",
                internal_details=str(e),
            ) from e