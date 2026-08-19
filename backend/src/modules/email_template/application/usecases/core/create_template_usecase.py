from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.modules.email_template.domain.events.template_domain_events import (
    TemplateCreatedEvent,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.modules.email_template.domain.services.template_category_domain_service import (
    TemplateCategoryDomainService,
)
from src.modules.email_template.presentation.schemas.template_schemas import (
    CreateTemplateRequestSchema,
)
from src.shared.exceptions.base_exceptions import (
    CreateError,
    DomainError,
    ServerError,
)
from src.shared.mediator.mediator import mediator


class CreateTemplateUseCase:
    """
    Use case for creating a custom email template.
    """

    def __init__(
        self,
        template_domain_service: TemplateDomainService,
        template_category_domain_service: TemplateCategoryDomainService,
    ):
        self.template_domain_service = template_domain_service
        self.template_category_domain_service = template_category_domain_service

    async def execute(
        self,
        payload: CreateTemplateRequestSchema,
        organization_id: int,
        actor_id: int,
    ) -> dict:
        """
        Creates an organization-owned custom template.
        """
        try:
            if payload.category_id is not None:
                category = await self.template_category_domain_service.get_available_category_by_id(
                    category_id=payload.category_id,
                    organization_id=organization_id,
                )
                if category is None:
                    raise CreateError(error="Template category is not available to this organization")

            template = TemplateEntity(
                organization_id=organization_id,
                category_id=payload.category_id,
                name=payload.name,
                description=payload.description,
                subject=payload.subject,
                preheader=payload.preheader,
                body_html=payload.body_html,
                from_name=payload.from_name,
                from_email=payload.from_email,
                tags=list(payload.tags),
                is_default=payload.is_default,
                smart_personalization_enabled=(
                    payload.smart_personalization_enabled
                ),
                created_by_id=actor_id,
            )

            created_template = (
                await self.template_domain_service
                .create_custom_template(
                    template
                )
            )

            if not created_template.id:
                raise CreateError(
                    error="Failed to create template"
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

            return {
                "uuid": created_template.uuid,
                "organization_id": (
                    created_template.organization_id
                ),
                "category_id": (
                    created_template.category_id
                ),
                "source_template_id": (
                    created_template.source_template_id
                ),
                "name": created_template.name,
                "description": (
                    created_template.description
                ),
                "subject": created_template.subject,
                "preheader": (
                    created_template.preheader
                ),
                "body_html": (
                    created_template.body_html
                ),
                "from_name": (
                    created_template.from_name
                ),
                "from_email": (
                    created_template.from_email
                ),
                "tags": list(
                    created_template.tags
                ),
                "template_type": (
                    created_template.template_type
                ),
                "status": created_template.status,
                "is_active": (
                    created_template.is_active
                ),
                "is_default": (
                    created_template.is_default
                ),
                "smart_personalization_enabled": (
                    created_template
                    .smart_personalization_enabled
                ),
                "published_at": (
                    created_template.published_at
                ),
                "archived_at": (
                    created_template.archived_at
                ),
                "created_by_id": (
                    created_template.created_by_id
                ),
                "updated_by_id": (
                    created_template.updated_by_id
                ),
                "created_at": (
                    created_template.created_at
                ),
                "updated_at": (
                    created_template.updated_at
                ),
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "An error occurred while creating template"
                ),
                internal_details=str(e),
            ) from e