from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.modules.email_template.domain.events.template_domain_events import (
    TemplateRestoredEvent,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError
from src.shared.mediator.mediator import mediator


class RestoreTemplateUseCase:
    """
    Use case for restoring an archived custom template back to draft.
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
        Restores an organization-owned archived custom template.
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
                    error="Failed to restore template",
                    internal_details="Template not found",
                )

            restored_template = (
                await self.template_domain_service.restore_custom_template(
                    template_id=template.id,
                    organization_id=organization_id,
                    actor_id=actor_id,
                )
            )

            if restored_template.id is None:
                raise ServerError(
                    error="Failed to restore template",
                    internal_details="Restored template id is missing",
                )

            restored_template.add_event(
                TemplateRestoredEvent(
                    template_id=restored_template.id,
                    template_uuid=restored_template.uuid,
                    organization_id=organization_id,
                    restored_by_id=actor_id,
                )
            )

            for event in restored_template.pull_events():
                await mediator.publish(event)

            return restored_template

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while restoring template",
                internal_details=str(e),
            ) from e
