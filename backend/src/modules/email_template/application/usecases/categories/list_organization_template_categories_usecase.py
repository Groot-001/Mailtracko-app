from src.modules.email_template.domain.entities.template_category_entity import (
    TemplateCategoryEntity,
)
from src.modules.email_template.domain.services.template_category_domain_service import (
    TemplateCategoryDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class ListOrganizationTemplateCategoriesUseCase:
    """List global categories plus categories owned by one organization."""

    def __init__(
        self,
        template_category_domain_service: TemplateCategoryDomainService,
    ) -> None:
        self.template_category_domain_service = template_category_domain_service

    async def execute(self, organization_id: int) -> list[TemplateCategoryEntity]:
        try:
            return await self.template_category_domain_service.list_available_categories(
                organization_id=organization_id
            )
        except DomainError:
            raise
        except Exception as exc:
            raise ServerError(
                error="Failed to list template categories",
                internal_details=str(exc),
            ) from exc
