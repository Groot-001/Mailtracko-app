from src.modules.email_template.domain.services.template_category_domain_service import (
    TemplateCategoryDomainService,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ServerError,
)


class GetTemplateDashboardSummaryUseCase:
    """
    Use case for retrieving template dashboard statistics.
    """

    def __init__(
        self,
        template_domain_service: TemplateDomainService,
        template_category_domain_service: TemplateCategoryDomainService,
    ):
        self.template_domain_service = (
            template_domain_service
        )
        self.template_category_domain_service = (
            template_category_domain_service
        )

    async def execute(
        self,
        organization_id: int,
    ) -> dict:
        """
        Returns template and category counts for the current organization.
        """
        try:
            template_counts = (
                await self.template_domain_service
                .get_dashboard_counts(
                    organization_id=organization_id,
                )
            )

            total_categories = (
                await self.template_category_domain_service
                .count_active_categories(organization_id=organization_id)
            )

            return {
                **template_counts,
                "total_categories": total_categories,
                # Campaign module does not exist yet.
                "used_in_campaigns": None,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "Failed to retrieve template dashboard summary"
                ),
                internal_details=str(e),
            ) from e