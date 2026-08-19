from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class GetSystemTemplateDetailsUseCase:
    """
    Use case for getting system template details.
    """

    def __init__(
        self,
        template_domain_service: TemplateDomainService,
    ):
        self.template_domain_service = template_domain_service

    async def execute(
        self,
        template_uuid: str,
    ) -> TemplateEntity:
        """
        Executes the use case to get system template details.
        """
        try:
            template = (
                await self.template_domain_service.get_system_template_by_uuid(
                    template_uuid
                )
            )

            if not template or not template.id:
                raise ServerError(
                    error="Error while retrieving system template details",
                    internal_details=(
                        f"No system template found with uuid {template_uuid}"
                    ),
                )

            return template

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "An error occurred while retrieving "
                    "system template details"
                ),
                internal_details=str(e),
            ) from e