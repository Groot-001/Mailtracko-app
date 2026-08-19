from src.modules.email_template.domain.entities.template_category_entity import (
    TemplateCategoryEntity,
)
from src.modules.email_template.domain.services.template_category_domain_service import (
    TemplateCategoryDomainService,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ServerError,
)


class ListTemplateCategoriesUseCase:
    """
    Use case for listing active system-template categories.
    """

    def __init__(
        self,
        template_category_domain_service: TemplateCategoryDomainService,
    ):
        self.template_category_domain_service = (
            template_category_domain_service
        )

    async def execute(
        self,
    ) -> list[TemplateCategoryEntity]:
        """
        Lists active categories for the system-template gallery.
        """
        try:
            categories = (
                await self.template_category_domain_service
                .list_active_categories()
            )

            return categories

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to list template categories",
                internal_details=str(e),
            ) from e