from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.modules.email_template.domain.events.template_domain_events import (
    TemplateArchivedEvent,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError
from src.shared.mediator.mediator import mediator


class ArchiveTemplateUseCase:
    """
    Use case for archiving a custom template.
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
        Archives a published custom template.
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
                    error="Failed to archive template",
                    internal_details="Template not found",
                )

            archived_template = (
                await self.template_domain_service.archive_custom_template(
                    template_id=template.id,
                    organization_id=organization_id,
                    actor_id=actor_id,
                )
            )

            if archived_template.id is None:
                raise ServerError(
                    error="Failed to archive template",
                    internal_details="Archived template id is missing",
                )

            archived_template.add_event(
                TemplateArchivedEvent(
                    template_id=archived_template.id,
                    template_uuid=archived_template.uuid,
                    organization_id=organization_id,
                    archived_by_id=actor_id,
                )
            )

            for event in archived_template.pull_events():
                await mediator.publish(event)

            return archived_template

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while archiving template",
                internal_details=str(e),
            ) from e