from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class ListSystemTemplatesUseCase:
    """
    Use case for listing system templates.
    """

    def __init__(
        self,
        template_domain_service: TemplateDomainService,
    ):
        self.template_domain_service = template_domain_service

    async def execute(
        self,
        *,
        category_id: int | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TemplateEntity], int]:
        """
        Lists active and published system templates.
        """
        try:
            templates, total = (
                await self.template_domain_service.list_system_paginated(
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
                error="Failed to list system templates",
                internal_details=str(e),
            ) from e