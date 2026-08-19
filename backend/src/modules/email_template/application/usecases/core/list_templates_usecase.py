from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class ListTemplatesUseCase:
    """
    Use case for listing organization-owned custom templates.
    """

    def __init__(
        self,
        template_domain_service: TemplateDomainService,
    ):
        self.template_domain_service = template_domain_service

    async def execute(
        self,
        *,
        organization_id: int,
        status: str | None = None,
        include_archived: bool = False,
        category_id: int | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TemplateEntity], int]:
        """
        Lists custom templates with filtering and pagination.
        """
        try:
            templates, total = (
                await self.template_domain_service.list_custom_paginated(
                    organization_id=organization_id,
                    status=status,
                    include_archived=include_archived,
                    category_id=category_id,
                    search=search,
                    limit=limit,
                    offset=offset,
                )
            )

            return templates, total

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to list templates",
                internal_details=str(e),
            ) from e