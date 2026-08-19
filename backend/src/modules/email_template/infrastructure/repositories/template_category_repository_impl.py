from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from src.modules.email_template.domain.entities.template_category_entity import (
    TemplateCategoryEntity,
)
from src.modules.email_template.domain.repositories.template_category_repository import (
    ITemplateCategoryRepository,
)
from src.modules.email_template.infrastructure.models.template_category_model import (
    TemplateCategoryModel,
)
from src.shared.exceptions.base_exceptions import ServerError
from src.shared.infrastructure.repository.base_repository import BaseRepository


class TemplateCategoryRepositoryImpl(
    BaseRepository[TemplateCategoryEntity],
    ITemplateCategoryRepository,
):
    """
    SQLAlchemy implementation of the template category repository.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.table_name = TemplateCategoryModel.__tablename__
        super().__init__(session, self.table_name)

    def to_row(self, entity: TemplateCategoryEntity) -> dict:
        """
        Convert a TemplateCategoryEntity to a database row.
        """
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "organization_id": entity.organization_id,
            "name": entity.name,
            "description": entity.description,
            "display_order": entity.display_order,
            "is_active": entity.is_active,
            "created_by_id": entity.created_by_id,
            "updated_by_id": entity.updated_by_id,
            "deleted_at": entity.deleted_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> TemplateCategoryEntity:
        """
        Convert a database row to TemplateCategoryEntity.
        """
        return TemplateCategoryEntity(
            id=row["id"],
            uuid=row["uuid"],
            organization_id=row.get("organization_id"),
            name=row["name"],
            description=row.get("description"),
            display_order=row["display_order"],
            is_active=row["is_active"],
            created_by_id=row.get("created_by_id"),
            updated_by_id=row.get("updated_by_id"),
            deleted_at=row.get("deleted_at"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def list_active(self) -> list[TemplateCategoryEntity]:
        """List active global categories used by the system-template gallery."""
        return await self._list_active_with_scope(organization_id=None, global_only=True)

    async def list_active_for_organization(
        self,
        organization_id: int,
    ) -> list[TemplateCategoryEntity]:
        """List global categories plus categories owned by one organization."""
        return await self._list_active_with_scope(
            organization_id=organization_id,
            global_only=False,
        )

    async def _list_active_with_scope(
        self,
        organization_id: int | None,
        global_only: bool,
    ) -> list[TemplateCategoryEntity]:
        scope_clause = "AND organization_id IS NULL"
        params: dict[str, object] = {}
        if not global_only and organization_id is not None:
            scope_clause = "AND (organization_id IS NULL OR organization_id = :organization_id)"
            params["organization_id"] = organization_id

        sql = text(
            f"SELECT * FROM {self.table_name} "
            "WHERE is_active = true "
            "AND deleted_at IS NULL "
            f"{scope_clause} "
            "ORDER BY CASE WHEN organization_id IS NULL THEN 0 ELSE 1 END, "
            "display_order ASC, name ASC, id ASC"
        )
        try:
            result = await self.session.execute(sql, params)
            return [self.to_entity(dict(row)) for row in result.mappings().all()]
        except SQLAlchemyError as exc:
            raise ServerError(
                error="Failed to list template categories",
                internal_details=str(exc),
            ) from exc

    async def find_active_by_name(
        self,
        name: str,
        organization_id: int | None,
    ) -> TemplateCategoryEntity | None:
        if organization_id is None:
            scope_clause = "organization_id IS NULL"
            params: dict[str, object] = {"name": name.strip().lower()}
        else:
            scope_clause = "organization_id = :organization_id"
            params = {
                "name": name.strip().lower(),
                "organization_id": organization_id,
            }

        sql = text(
            f"SELECT * FROM {self.table_name} "
            "WHERE LOWER(TRIM(name)) = :name "
            "AND is_active = true AND deleted_at IS NULL "
            f"AND {scope_clause} LIMIT 1"
        )
        try:
            result = await self.session.execute(sql, params)
            row = result.mappings().first()
            return self.to_entity(dict(row)) if row else None
        except SQLAlchemyError as exc:
            raise ServerError(
                error="Failed to find template category",
                internal_details=str(exc),
            ) from exc

    async def count_active(self, organization_id: int | None = None) -> int:
        scope_clause = "AND organization_id IS NULL"
        params: dict[str, object] = {}
        if organization_id is not None:
            scope_clause = "AND (organization_id IS NULL OR organization_id = :organization_id)"
            params["organization_id"] = organization_id

        sql = text(
            f"SELECT COUNT(*) FROM {self.table_name} "
            "WHERE is_active = true AND deleted_at IS NULL "
            f"{scope_clause}"
        )
        try:
            result = await self.session.execute(sql, params)
            return int(result.scalar_one())
        except SQLAlchemyError as exc:
            raise ServerError(
                error="Failed to count template categories",
                internal_details=str(exc),
            ) from exc
