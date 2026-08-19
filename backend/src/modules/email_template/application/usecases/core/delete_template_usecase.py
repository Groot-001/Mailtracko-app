from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.modules.email_template.domain.events.template_domain_events import (
    TemplateDeletedEvent,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError
from src.shared.mediator.mediator import mediator


class DeleteTemplateUseCase:
    """
    Use case for soft-deleting a custom template.
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
        actor_id: int,
    ) -> TemplateEntity:
        """
        Soft-deletes an organization-owned custom template.
        """
        try:
            template = (
                await self.template_domain_service.get_custom_template_by_uuid(
                    template_uuid=template_uuid,
                    organization_id=organization_id,
                )
            )

            if not template or template.id is None:
                raise ServerError(
                    error="Failed to delete template",
                    internal_details="Template not found",
                )

            deleted_template = (
                await self.template_domain_service.delete_custom_template(
                    template_id=template.id,
                    organization_id=organization_id,
                    actor_id=actor_id,
                )
            )

            if deleted_template.id is None:
                raise ServerError(
                    error="Failed to delete template",
                    internal_details="Deleted template id is missing",
                )

            deleted_template.add_event(
                TemplateDeletedEvent(
                    template_id=deleted_template.id,
                    template_uuid=deleted_template.uuid,
                    organization_id=organization_id,
                    deleted_by_id=actor_id,
                )
            )

            for event in deleted_template.pull_events():
                await mediator.publish(event)

            return deleted_template

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while deleting template",
                internal_details=str(e),
            ) from e