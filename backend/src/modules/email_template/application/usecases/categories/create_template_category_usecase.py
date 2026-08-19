from src.modules.email_template.domain.entities.template_category_entity import (
    TemplateCategoryEntity,
)
from src.modules.email_template.domain.services.template_category_domain_service import (
    TemplateCategoryDomainService,
)
from src.modules.email_template.presentation.schemas.template_schemas import (
    CreateTemplateCategoryRequestSchema,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class CreateTemplateCategoryUseCase:
    """Create an organization-owned template category."""

    def __init__(
        self,
        template_category_domain_service: TemplateCategoryDomainService,
    ) -> None:
        self.template_category_domain_service = template_category_domain_service

    async def execute(
        self,
        payload: CreateTemplateCategoryRequestSchema,
        organization_id: int,
        actor_id: int,
    ) -> TemplateCategoryEntity:
        try:
            category = TemplateCategoryEntity(
                organization_id=organization_id,
                name=payload.name.strip(),
                description=(payload.description.strip() if payload.description else None),
                display_order=payload.display_order,
                created_by_id=actor_id,
            )
            return await self.template_category_domain_service.create_template_category(
                category
            )
        except DomainError:
            raise
        except Exception as exc:
            raise ServerError(
                error="Failed to create template category",
                internal_details=str(exc),
            ) from exc
