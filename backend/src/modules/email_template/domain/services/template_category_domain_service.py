from src.modules.email_template.domain.entities.template_category_entity import (
    TemplateCategoryEntity,
)
from src.modules.email_template.domain.repositories.template_category_repository import (
    ITemplateCategoryRepository,
)
from src.shared.exceptions.base_exceptions import (
    CreateError,
    DomainError,
    InvalidError,
    ServerError,
    UpdateError,
)


class TemplateCategoryDomainService:
    """
    Service class for template category domain logic.
    """

    def __init__(self, repository: ITemplateCategoryRepository):
        self.repository = repository

    async def create_template_category(
        self,
        category_entity: TemplateCategoryEntity,
    ) -> TemplateCategoryEntity:
        """
        Creates a global or organization-owned template category.
        """
        try:
            self._validate_category_name(category_entity.name)
            self._validate_display_order(category_entity.display_order)

            existing = await self.repository.find_active_by_name(
                name=category_entity.name,
                organization_id=category_entity.organization_id,
            )
            if not existing and category_entity.organization_id is not None:
                existing = await self.repository.find_active_by_name(
                    name=category_entity.name,
                    organization_id=None,
                )
            if existing:
                raise InvalidError(
                    error="A template category with this name already exists"
                )

            category_entity.name = category_entity.name.strip()
            category_entity.is_active = True

            return await self.repository.add(category_entity)

        except DomainError:
            raise
        except Exception as e:
            raise CreateError(
                error="Failed to create template category",
                internal_details=str(e),
            ) from e

    async def update_template_category(
        self,
        category_entity: TemplateCategoryEntity,
        actor_id: int,
    ) -> TemplateCategoryEntity:
        """
        Updates template category details.
        """
        try:
            if not category_entity.id:
                raise InvalidError(
                    error="Template category id is required"
                )

            self._validate_category_name(category_entity.name)
            self._validate_display_order(category_entity.display_order)

            category_entity.updated_by_id = actor_id
            category_entity.mark_updated()

            return await self.repository.update(category_entity)

        except DomainError:
            raise
        except Exception as e:
            raise UpdateError(
                error="Failed to update template category",
                internal_details=str(e),
            ) from e

    async def activate_template_category(
        self,
        category_id: int,
        actor_id: int,
    ) -> TemplateCategoryEntity:
        """
        Activates a template category.
        """
        try:
            category = await self.repository.get_by(
                id=category_id,
                deleted_at=None,
            )

            if not category or not category.id:
                raise InvalidError(
                    error="Template category not found"
                )

            category.is_active = True
            category.updated_by_id = actor_id
            category.mark_updated()

            return await self.repository.update(category)

        except DomainError:
            raise
        except Exception as e:
            raise UpdateError(
                error="Failed to activate template category",
                internal_details=str(e),
            ) from e

    async def list_active_categories(
        self,
    ) -> list[TemplateCategoryEntity]:
        """List active global categories in gallery display order."""
        return await self.repository.list_active()

    async def list_available_categories(
        self,
        organization_id: int,
    ) -> list[TemplateCategoryEntity]:
        """List active global and organization-owned categories."""
        return await self.repository.list_active_for_organization(organization_id)

    async def get_available_category_by_id(
        self,
        category_id: int,
        organization_id: int,
    ) -> TemplateCategoryEntity | None:
        """Return a category only when it is global or belongs to the organization."""
        category = await self.repository.get_by(
            id=category_id,
            is_active=True,
            deleted_at=None,
        )
        if not category:
            return None
        if category.organization_id not in (None, organization_id):
            return None
        return category

    async def deactivate_template_category(
        self,
        category_id: int,
        actor_id: int,
    ) -> TemplateCategoryEntity:
        """
        Deactivates a template category.
        """
        try:
            category = await self.repository.get_by(
                id=category_id,
                deleted_at=None,
            )

            if not category or not category.id:
                raise InvalidError(
                    error="Template category not found"
                )

            category.is_active = False
            category.updated_by_id = actor_id
            category.mark_updated()

            return await self.repository.update(category)

        except DomainError:
            raise
        except Exception as e:
            raise UpdateError(
                error="Failed to deactivate template category",
                internal_details=str(e),
            ) from e

    async def get_template_category_by_id(
        self,
        category_id: int,
    ) -> TemplateCategoryEntity | None:
        """
        Retrieves an active template category by ID.
        """
        try:
            return await self.repository.get_by(
                id=category_id,
                is_active=True,
                deleted_at=None,
            )

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to retrieve template category",
                internal_details=str(e),
            ) from e

    async def list_active(
        self,
    ) -> list[TemplateCategoryEntity]:
        """
        Lists active and non-deleted template categories.
        """
        try:
            return await self.repository.list_active()

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to list template categories",
                internal_details=str(e),
            ) from e

    def _validate_category_name(
        self,
        name: str,
    ) -> None:
        """
        Validates template category name.
        """
        if not name or not name.strip():
            raise InvalidError(
                error="Template category name is required"
            )

        if len(name.strip()) > 50:
            raise InvalidError(
                error="Template category name cannot exceed 50 characters"
            )

    def _validate_display_order(
        self,
        display_order: int,
    ) -> None:
        """
        Validates template category display order.
        """
        if display_order < 0:
            raise InvalidError(
                error="Template category display order cannot be negative"
            )

    async def count_active_categories(
        self,
        organization_id: int | None = None,
    ) -> int:
        """
        Counts active template categories.
        """
        try:
            return await self.repository.count_active(organization_id=organization_id)

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error=(
                    "Failed to count active template categories"
                ),
                internal_details=str(e),
            ) from e