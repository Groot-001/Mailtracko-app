from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.modules.email_template.domain.events.template_domain_events import (
    TemplateCreatedEvent,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.shared.exceptions.base_exceptions import (
    CreateError,
    DomainError,
    ServerError,
)
from src.shared.mediator.mediator import mediator


class CopySystemTemplateUseCase:
    """
    Use case for copying a system template into an organization.
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
        Copies a system template as an organization-owned custom draft.

        Downloadable attachment rows are not copied. Inline image URLs
        already present in body_html remain unchanged.
        """
        try:
            source_template = (
                await self.template_domain_service
                .get_system_template_by_uuid(
                    template_uuid
                )
            )

            if (
                not source_template
                or source_template.id is None
            ):
                raise CreateError(
                    error=(
                        "Failed to copy system template"
                    ),
                    internal_details=(
                        "No system template found with uuid "
                        f"{template_uuid}"
                    ),
                )

            copied_template = TemplateEntity(
                organization_id=organization_id,
                category_id=source_template.category_id,
                source_template_id=source_template.id,
                name=(
                    f"{source_template.name} Copy"
                ),
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
                    copied_template
                )
            )

            if not created_template.id:
                raise CreateError(
                    error=(
                        "Failed to copy system template"
                    )
                )

            created_template.add_event(
                TemplateCreatedEvent(
                    template_id=created_template.id,
                    template_uuid=created_template.uuid,
                    organization_id=organization_id,
                    created_by_id=actor_id,
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
                    "An error occurred while copying "
                    "system template"
                ),
                internal_details=str(e),
            ) from e