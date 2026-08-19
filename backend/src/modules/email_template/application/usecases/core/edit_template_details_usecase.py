from typing import Any

from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.modules.email_template.domain.events.template_domain_events import (
    TemplateUpdatedEvent,
)
from src.modules.email_template.domain.services.template_domain_service import (
    TemplateDomainService,
)
from src.modules.email_template.domain.services.template_category_domain_service import (
    TemplateCategoryDomainService,
)
from src.modules.email_template.presentation.schemas.template_schemas import (
    UpdateTemplateRequestSchema,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ServerError,
)
from src.shared.mediator.mediator import mediator


class EditTemplateDetailsUseCase:
    """
    Use case for editing custom template details.
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
        template_uuid: str,
        payload: UpdateTemplateRequestSchema,
        organization_id: int,
        actor_id: int,
    ) -> TemplateEntity:
        """
        Applies permitted custom-template changes.
        """
        try:
            template = (
                await self.template_domain_service
                .get_custom_template_by_uuid(
                    template_uuid=template_uuid,
                    organization_id=organization_id,
                )
            )

            if not template or template.id is None:
                raise ServerError(
                    error=(
                        "Error while retrieving template details"
                    ),
                    internal_details=(
                        f"No template found with uuid "
                        f"{template_uuid}"
                    ),
                )

            fields = payload.model_dump(
                exclude_unset=True
            )

            if fields.get("category_id") is not None:
                category = await self.template_category_domain_service.get_available_category_by_id(
                    category_id=fields["category_id"],
                    organization_id=organization_id,
                )
                if category is None:
                    raise ServerError(error="Template category is not available to this organization")

            updated_template = (
                await self._apply_template_changes(
                    template=template,
                    fields=fields,
                    actor_id=actor_id,
                )
            )

            if updated_template.id is None:
                raise ServerError(
                    error=(
                        "Failed to edit template details"
                    ),
                    internal_details=(
                        "Updated template id is missing"
                    ),
                )

            updated_template.add_event(
                TemplateUpdatedEvent(
                    template_id=updated_template.id,
                    template_uuid=updated_template.uuid,
                    organization_id=organization_id,
                    updated_by_id=actor_id,
                )
            )

            for event in updated_template.pull_events():
                await mediator.publish(
                    event
                )

            return updated_template

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "Failed to edit template details"
                ),
                internal_details=str(e),
            ) from e

    async def _apply_template_changes(
        self,
        template: TemplateEntity,
        fields: dict[str, Any],
        actor_id: int,
    ) -> TemplateEntity:
        """
        Updates allowed custom-template fields.
        """
        if not fields:
            return template

        for key, value in fields.items():
            if hasattr(value, "value"):
                value = value.value

            if key == "tags" and value is not None:
                value = list(value)

            setattr(
                template,
                key,
                value,
            )

        return await self.template_domain_service.update_custom_template(
            template,
            actor_id,
        )