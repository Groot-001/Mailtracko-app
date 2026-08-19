from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.modules.email_template.domain.events.template_domain_events import (
    TemplateDuplicatedEvent,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.modules.email_template.presentation.schemas.template_schemas import (
    DuplicateTemplateRequestSchema,
)
from src.shared.exceptions.base_exceptions import (
    CreateError,
    DomainError,
    ServerError,
)
from src.shared.mediator.mediator import mediator


class DuplicateTemplateUseCase:
    """
    Use case for duplicating a custom template.
    """

    def __init__(
        self,
        template_domain_service: TemplateDomainService,
    ):
        self.template_domain_service = template_domain_service

    async def execute(
        self,
        template_uuid: str,
        payload: DuplicateTemplateRequestSchema,
        organization_id: int,
        actor_id: int,
    ) -> TemplateEntity:
        """
        Duplicates a custom template as a new custom draft.

        Downloadable attachment rows are not copied. Existing inline-image
        URLs remain inside body_html.
        """
        try:
            source_template = (
                await self.template_domain_service
                .get_custom_template_by_uuid(
                    template_uuid=template_uuid,
                    organization_id=organization_id,
                )
            )

            if (
                not source_template
                or source_template.id is None
            ):
                raise CreateError(
                    error=(
                        "Failed to duplicate template"
                    ),
                    internal_details=(
                        "Source template not found"
                    ),
                )

            duplicate_name = (
                payload.name
                if payload.name
                else f"{source_template.name} Copy"
            )

            duplicated_template = TemplateEntity(
                organization_id=organization_id,
                category_id=source_template.category_id,
                source_template_id=source_template.id,
                name=duplicate_name,
                description=(
                    source_template.description
                ),
                subject=source_template.subject,
                preheader=source_template.preheader,
                body_html=source_template.body_html,
                from_name=source_template.from_name,
                from_email=source_template.from_email,
                tags=list(source_template.tags),
                is_default=False,
                smart_personalization_enabled=(
                    source_template
                    .smart_personalization_enabled
                ),
                created_by_id=actor_id,
            )

            created_template = (
                await self.template_domain_service
                .create_custom_template(
                    duplicated_template
                )
            )

            if created_template.id is None:
                raise CreateError(
                    error=(
                        "Failed to duplicate template"
                    ),
                    internal_details=(
                        "Duplicated template id is missing"
                    ),
                )

            created_template.add_event(
                TemplateDuplicatedEvent(
                    template_id=created_template.id,
                    template_uuid=created_template.uuid,
                    source_template_id=source_template.id,
                    organization_id=organization_id,
                    duplicated_by_id=actor_id,
                )
            )

            for event in created_template.pull_events():
                await mediator.publish(
                    event
                )

            return created_template

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "An error occurred while duplicating template"
                ),
                internal_details=str(e),
            ) from e