from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.modules.email_template.domain.enums.template_enums import (
    TemplateStatusEnum,
    TemplateTypeEnum,
)
from src.modules.email_template.domain.repositories.template_repository import (
    ITemplateRepository,
)
from src.shared.exceptions.base_exceptions import (
    CreateError,
    DomainError,
    InvalidError,
    ServerError,
    UpdateError,
)


class TemplateDomainService:
    """
    Service class for template domain logic.
    """

    VALID_STATUSES = {
        TemplateStatusEnum.DRAFT.value,
        TemplateStatusEnum.PUBLISHED.value,
        TemplateStatusEnum.ARCHIVED.value,
    }

    def __init__(
        self,
        repository: ITemplateRepository,
    ):
        self.repository = repository

    async def create_custom_template(
        self,
        template_entity: TemplateEntity,
    ) -> TemplateEntity:
        """
        Creates a new organization-owned custom template.

        New custom, copied, and duplicated templates always start as drafts.
        """
        try:
            organization_id = self._get_required_organization_id(
                template_entity
            )

            self._validate_template_name(
                template_entity.name
            )
            self._validate_optional_fields(
                template_entity
            )

            template_entity.template_type = (
                TemplateTypeEnum.CUSTOM.value
            )
            template_entity.status = (
                TemplateStatusEnum.DRAFT.value
            )
            template_entity.is_active = True
            template_entity.published_at = None
            template_entity.archived_at = None

            if template_entity.is_default:
                actor_id = template_entity.created_by_id

                if actor_id is None:
                    raise InvalidError(
                        error=(
                            "Created by id is required for "
                            "default template"
                        )
                    )

                await self.repository.unset_default_for_organization(
                    organization_id=organization_id,
                    updated_by_id=actor_id,
                )

            return await self.repository.add(
                template_entity
            )

        except DomainError:
            raise
        except Exception as e:
            raise CreateError(
                error="Failed to create template",
                internal_details=str(e),
            ) from e

    async def update_custom_template(
        self,
        template_entity: TemplateEntity,
        actor_id: int,
    ) -> TemplateEntity:
        """
        Updates an organization-owned custom template.
        """
        try:
            if not template_entity.id:
                raise InvalidError(
                    error="Template id is required"
                )

            organization_id = self._get_required_organization_id(
                template_entity
            )

            self._ensure_template_is_custom(
                template_entity
            )
            self._ensure_template_is_draft_for_edit(
                template_entity
            )
            self._validate_template_name(
                template_entity.name
            )
            self._validate_optional_fields(
                template_entity
            )

            if template_entity.is_default:
                await self.repository.unset_default_for_organization(
                    organization_id=organization_id,
                    updated_by_id=actor_id,
                    exclude_template_id=template_entity.id,
                )

            template_entity.updated_by_id = actor_id
            template_entity.mark_updated()

            return await self.repository.update(
                template_entity
            )

        except DomainError:
            raise
        except Exception as e:
            raise UpdateError(
                error="Failed to update template",
                internal_details=str(e),
            ) from e

    async def publish_custom_template(
        self,
        template_id: int,
        organization_id: int,
        actor_id: int,
    ) -> TemplateEntity:
        """
        Publishes an organization-owned custom template.
        """
        try:
            template = await self.repository.get_by(
                id=template_id,
                organization_id=organization_id,
                deleted_at=None,
            )

            if not template or not template.id:
                raise InvalidError(
                    error="Template not found"
                )

            self._ensure_template_is_custom(
                template
            )
            self._ensure_template_can_be_published(
                template
            )

            if (
                template.status
                == TemplateStatusEnum.PUBLISHED.value
            ):
                raise InvalidError(
                    error="Template is already published"
                )

            template.updated_by_id = actor_id
            template.publish()

            return await self.repository.update(
                template
            )

        except DomainError:
            raise
        except Exception as e:
            raise UpdateError(
                error="Failed to publish template",
                internal_details=str(e),
            ) from e

    async def archive_custom_template(
        self,
        template_id: int,
        organization_id: int,
        actor_id: int,
    ) -> TemplateEntity:
        """
        Archives a published custom template.
        """
        try:
            template = await self.repository.get_by(
                id=template_id,
                organization_id=organization_id,
                deleted_at=None,
            )

            if not template or not template.id:
                raise InvalidError(
                    error="Template not found"
                )

            self._ensure_template_is_custom(
                template
            )
            await self._ensure_template_not_used_in_campaigns(
                template_id=template.id,
                organization_id=organization_id,
                operation="archived",
            )

            if (
                template.status
                != TemplateStatusEnum.PUBLISHED.value
            ):
                raise InvalidError(
                    error=(
                        "Only published template can be archived"
                    )
                )

            template.is_default = False
            template.updated_by_id = actor_id
            template.archive()

            return await self.repository.update(
                template
            )

        except DomainError:
            raise
        except Exception as e:
            raise UpdateError(
                error="Failed to archive template",
                internal_details=str(e),
            ) from e

    async def delete_custom_template(
        self,
        template_id: int,
        organization_id: int,
        actor_id: int,
    ) -> TemplateEntity:
        """
        Soft-deletes an organization-owned custom template.
        """
        try:
            template = await self.repository.get_by(
                id=template_id,
                organization_id=organization_id,
                deleted_at=None,
            )

            if not template or not template.id:
                raise InvalidError(
                    error="Template not found"
                )

            self._ensure_template_is_custom(
                template
            )
            await self._ensure_template_not_used_in_campaigns(
                template_id=template.id,
                organization_id=organization_id,
                operation="deleted",
            )

            template.is_active = False
            template.is_default = False
            template.updated_by_id = actor_id
            template.soft_delete()
            template.mark_updated()

            return await self.repository.update(
                template
            )

        except DomainError:
            raise
        except Exception as e:
            raise UpdateError(
                error="Failed to delete template",
                internal_details=str(e),
            ) from e

    async def restore_custom_template(
        self,
        template_id: int,
        organization_id: int,
        actor_id: int,
    ) -> TemplateEntity:
        """
        Restores an archived custom template back to draft.
        """
        try:
            template = await self.repository.get_by(
                id=template_id,
                organization_id=organization_id,
                deleted_at=None,
            )

            if not template or not template.id:
                raise InvalidError(
                    error="Template not found"
                )

            self._ensure_template_is_custom(
                template
            )

            if (
                template.status
                != TemplateStatusEnum.ARCHIVED.value
            ):
                raise InvalidError(
                    error="Only archived template can be restored"
                )

            template.status = TemplateStatusEnum.DRAFT.value
            template.archived_at = None
            template.published_at = None
            template.is_default = False
            template.updated_by_id = actor_id
            template.mark_updated()

            return await self.repository.update(
                template
            )

        except DomainError:
            raise
        except Exception as e:
            raise UpdateError(
                error="Failed to restore template",
                internal_details=str(e),
            ) from e

    async def get_custom_template_by_id(
        self,
        template_id: int,
        organization_id: int,
    ) -> TemplateEntity | None:
        """
        Retrieves a custom template by ID and organization ID.
        """
        try:
            template = await self.repository.get_by(
                id=template_id,
                organization_id=organization_id,
                deleted_at=None,
            )

            if (
                template
                and template.template_type
                != TemplateTypeEnum.CUSTOM.value
            ):
                return None

            return template

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "Failed to retrieve custom template"
                ),
                internal_details=str(e),
            ) from e

    async def get_custom_template_by_uuid(
        self,
        template_uuid: str,
        organization_id: int,
    ) -> TemplateEntity | None:
        """
        Retrieves a custom template by UUID and organization ID.
        """
        try:
            return await self.repository.get_custom_by_uuid(
                template_uuid=template_uuid,
                organization_id=organization_id,
            )

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "Failed to retrieve custom template"
                ),
                internal_details=str(e),
            ) from e

    async def list_custom_paginated(
        self,
        *,
        organization_id: int,
        status: str | None = None,
        include_archived: bool = False,
        category_id: int | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TemplateEntity], int]:
        """
        Lists organization-owned custom templates.
        """
        try:
            if status:
                self._validate_status(
                    status
                )

            return await self.repository.list_custom_paginated(
                organization_id=organization_id,
                status=status,
                include_archived=include_archived,
                category_id=category_id,
                search=search,
                limit=limit,
                offset=offset,
            )

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "Failed to list custom templates"
                ),
                internal_details=str(e),
            ) from e

    async def get_system_template_by_uuid(
        self,
        template_uuid: str,
    ) -> TemplateEntity | None:
        """
        Retrieves an active published system template by UUID.
        """
        try:
            return await self.repository.get_system_by_uuid(
                template_uuid
            )

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "Failed to retrieve system template"
                ),
                internal_details=str(e),
            ) from e

    async def list_system_paginated(
        self,
        *,
        category_id: int | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TemplateEntity], int]:
        """
        Lists active published system templates.
        """
        try:
            return await self.repository.list_system_paginated(
                category_id=category_id,
                search=search,
                limit=limit,
                offset=offset,
            )

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "Failed to list system templates"
                ),
                internal_details=str(e),
            ) from e

    async def get_dashboard_counts(
        self,
        *,
        organization_id: int,
    ) -> dict[str, int]:
        """
        Returns custom-template dashboard counts.
        """
        try:
            return await self.repository.get_dashboard_counts(
                organization_id=organization_id,
            )

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "Failed to retrieve template dashboard counts"
                ),
                internal_details=str(e),
            ) from e

    def _get_required_organization_id(
        self,
        template_entity: TemplateEntity,
    ) -> int:
        """
        Returns the required organization ID for a custom template.
        """
        if not template_entity.organization_id:
            raise InvalidError(
                error=(
                    "Organization id is required for custom template"
                )
            )

        return template_entity.organization_id

    def _ensure_template_is_custom(
        self,
        template_entity: TemplateEntity,
    ) -> None:
        """
        Ensures a system template cannot be modified through custom flow.
        """
        if (
            template_entity.template_type
            != TemplateTypeEnum.CUSTOM.value
        ):
            raise InvalidError(
                error=(
                    "System template cannot be modified directly"
                )
            )

    def _ensure_template_can_be_published(
        self,
        template_entity: TemplateEntity,
    ) -> None:
        """
        Ensures the template contains required publishable content.
        """
        self._validate_template_name(
            template_entity.name
        )

        if (
            not template_entity.subject
            or not template_entity.subject.strip()
        ):
            raise InvalidError(
                error=(
                    "Template subject is required before publishing"
                )
            )

        if (
            not template_entity.body_html
            or not template_entity.body_html.strip()
        ):
            raise InvalidError(
                error=(
                    "Template body is required before publishing"
                )
            )

        self._validate_optional_fields(
            template_entity
        )

    def _ensure_template_is_draft_for_edit(
        self,
        template_entity: TemplateEntity,
    ) -> None:
        """
        Ensures only draft templates can be edited.
        """
        if (
            template_entity.status
            != TemplateStatusEnum.DRAFT.value
        ):
            raise InvalidError(
                error="Only draft templates can be edited"
            )

    async def _ensure_template_not_used_in_campaigns(
        self,
        *,
        template_id: int,
        organization_id: int,
        operation: str,
    ) -> None:
        """
        Prevents lifecycle actions when campaigns still reference the template.
        """
        usage_count = await self.repository.count_campaign_usages(
            template_id=template_id,
            organization_id=organization_id,
        )
        if usage_count > 0:
            raise InvalidError(
                error=(
                    f"This template is currently being used by an unfinished campaign and cannot be {operation} until the campaign is finished"
                ),
                errors={"code": "TEMPLATE_IN_USE", "usage_count": usage_count},
            )

    def _validate_template_name(
        self,
        name: str,
    ) -> None:
        """
        Validates template name.
        """
        if not name or not name.strip():
            raise InvalidError(
                error="Template name is required"
            )

        if len(name.strip()) > 150:
            raise InvalidError(
                error=(
                    "Template name cannot exceed 150 characters"
                )
            )

    def _validate_optional_fields(
        self,
        template_entity: TemplateEntity,
    ) -> None:
        """
        Validates optional template settings.
        """
        if (
            template_entity.subject
            and len(template_entity.subject) > 255
        ):
            raise InvalidError(
                error=(
                    "Template subject cannot exceed 255 characters"
                )
            )

        if (
            template_entity.preheader
            and len(template_entity.preheader) > 255
        ):
            raise InvalidError(
                error=(
                    "Template preheader cannot exceed 255 characters"
                )
            )

        if template_entity.from_name:
            sender_name = template_entity.from_name.strip()
            if len(sender_name) > 50:
                raise InvalidError(
                    error="Default sender name cannot exceed 50 characters"
                )
            if not any(character.isalpha() for character in sender_name):
                raise InvalidError(
                    error="Default sender name must contain at least one letter"
                )

        if (
            template_entity.from_email
            and len(template_entity.from_email) > 50
        ):
            raise InvalidError(
                error="Default sender email cannot exceed 50 characters"
            )

        if len(template_entity.tags) > 20:
            raise InvalidError(
                error=(
                    "Template cannot contain more than 20 tags"
                )
            )

        for tag in template_entity.tags:
            if len(tag) > 50:
                raise InvalidError(
                    error=(
                        "Template tag cannot exceed 50 characters"
                    )
                )

    def _validate_status(
        self,
        status: str,
    ) -> None:
        """
        Validates template status.
        """
        if status not in self.VALID_STATUSES:
            raise InvalidError(
                error="Invalid template status"
            )