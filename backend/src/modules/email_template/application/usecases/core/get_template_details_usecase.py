from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class GetTemplateDetailsUseCase:
    """
    Use case for getting custom template details.
    """

    def __init__(
        self,
        template_domain_service: TemplateDomainService,
    ):
        self.template_domain_service = template_domain_service

    async def execute(
        self,
        template_uuid: str,
        organization_id: int,
    ) -> TemplateEntity:
        """
        Retrieves a custom template belonging to the current organization.
        """
        try:
            template = (
                await self.template_domain_service.get_custom_template_by_uuid(
                    template_uuid=template_uuid,
                    organization_id=organization_id,
                )
            )

            if not template or not template.id:
                raise ServerError(
                    error="Error while retrieving template details",
                    internal_details=(
                        f"No template found with uuid {template_uuid}"
                    ),
                )

            return template

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while retrieving template details",
                internal_details=str(e),
            ) from e