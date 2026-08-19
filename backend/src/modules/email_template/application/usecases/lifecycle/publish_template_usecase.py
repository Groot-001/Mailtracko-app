from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.modules.email_template.domain.events.template_domain_events import (
    TemplatePublishedEvent,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError
from src.shared.mediator.mediator import mediator


class PublishTemplateUseCase:
    """
    Use case for publishing a custom template.
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
        Publishes an organization-owned custom template.
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
                    error="Failed to publish template",
                    internal_details="Template not found",
                )

            published_template = (
                await self.template_domain_service.publish_custom_template(
                    template_id=template.id,
                    organization_id=organization_id,
                    actor_id=actor_id,
                )
            )

            if published_template.id is None:
                raise ServerError(
                    error="Failed to publish template",
                    internal_details="Published template id is missing",
                )

            published_template.add_event(
                TemplatePublishedEvent(
                    template_id=published_template.id,
                    template_uuid=published_template.uuid,
                    organization_id=organization_id,
                    published_by_id=actor_id,
                )
            )

            for event in published_template.pull_events():
                await mediator.publish(event)

            return published_template

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while publishing template",
                internal_details=str(e),
            ) from e