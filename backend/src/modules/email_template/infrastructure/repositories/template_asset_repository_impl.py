from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from src.modules.email_template.domain.entities.template_asset_entity import (
    TemplateAssetEntity,
)
from src.modules.email_template.domain.repositories.template_asset_repository import (
    ITemplateAssetRepository,
)
from src.modules.email_template.infrastructure.models.template_asset_model import (
    TemplateAssetModel,
)
from src.shared.exceptions.base_exceptions import ServerError
from src.shared.infrastructure.repository.base_repository import BaseRepository


class TemplateAssetRepositoryImpl(
    BaseRepository[TemplateAssetEntity],
    ITemplateAssetRepository,
):
    """
    SQLAlchemy implementation of the template asset repository.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.table_name = TemplateAssetModel.__tablename__
        super().__init__(session, self.table_name)

    def to_row(self, entity: TemplateAssetEntity) -> dict:
        """
        Convert a TemplateAssetEntity to a database row.
        """
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "template_id": entity.template_id,
            "organization_id": entity.organization_id,
            "original_filename": entity.original_filename,
            "storage_key": entity.storage_key,
            "file_url": entity.file_url,
            "content_type": entity.content_type,
            "file_size": entity.file_size,
            "asset_type": entity.asset_type,
            "usage": entity.usage,
            "is_active": entity.is_active,
            "uploaded_by_id": entity.uploaded_by_id,
            "deleted_at": entity.deleted_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> TemplateAssetEntity:
        """
        Convert a database row to TemplateAssetEntity.
        """
        return TemplateAssetEntity(
            id=row["id"],
            uuid=row["uuid"],
            template_id=row["template_id"],
            organization_id=row.get("organization_id"),
            original_filename=row["original_filename"],
            storage_key=row["storage_key"],
            file_url=row["file_url"],
            content_type=row["content_type"],
            file_size=row["file_size"],
            asset_type=row["asset_type"],
            usage=row["usage"],
            is_active=row["is_active"],
            uploaded_by_id=row.get("uploaded_by_id"),
            deleted_at=row.get("deleted_at"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_by_uuid_and_template_id(
        self,
        *,
        asset_uuid: str,
        template_id: int,
        organization_id: int | None,
    ) -> TemplateAssetEntity | None:
        """
        Retrieves an active template asset by UUID and template ownership.
        """
        where_clauses = [
            "uuid = :asset_uuid",
            "template_id = :template_id",
            "is_active = true",
            "deleted_at IS NULL",
        ]

        params: dict[str, int | str] = {
            "asset_uuid": asset_uuid,
            "template_id": template_id,
        }

        if organization_id is None:
            where_clauses.append("organization_id IS NULL")
        else:
            where_clauses.append("organization_id = :organization_id")
            params["organization_id"] = organization_id

        where_sql = " AND ".join(where_clauses)

        sql = text(
            f"SELECT * FROM {self.table_name} "
            f"WHERE {where_sql} "
            "LIMIT 1"
        )

        try:
            result = await self.session.execute(sql, params)
            row = result.mappings().one_or_none()
            return self.to_entity(dict(row)) if row else None

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to fetch template asset",
                internal_details=str(e),
            ) from e

    async def list_paginated(
        self,
        *,
        template_id: int,
        organization_id: int | None,
        usage: str | None = None,
        asset_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TemplateAssetEntity], int]:
        """
        Lists active template assets with pagination.
        """
        where_clauses = [
            "template_id = :template_id",
            "is_active = true",
            "deleted_at IS NULL",
        ]

        params: dict[str, int | str] = {
            "template_id": template_id,
            "limit": limit,
            "offset": offset,
        }

        if organization_id is None:
            where_clauses.append("organization_id IS NULL")
        else:
            where_clauses.append("organization_id = :organization_id")
            params["organization_id"] = organization_id

        if usage:
            where_clauses.append("usage = :usage")
            params["usage"] = usage

        if asset_type:
            where_clauses.append("asset_type = :asset_type")
            params["asset_type"] = asset_type

        where_sql = " AND ".join(where_clauses)

        list_sql = text(
            f"SELECT * FROM {self.table_name} "
            f"WHERE {where_sql} "
            "ORDER BY id DESC "
            "LIMIT :limit OFFSET :offset"
        )

        count_sql = text(
            f"SELECT COUNT(*) FROM {self.table_name} "
            f"WHERE {where_sql}"
        )

        try:
            list_result = await self.session.execute(list_sql, params)
            rows = list_result.mappings().all()

            count_result = await self.session.execute(
                count_sql,
                {
                    key: value
                    for key, value in params.items()
                    if key not in {"limit", "offset"}
                },
            )

            total = int(count_result.scalar_one())

            return [
                self.to_entity(dict(row))
                for row in rows
            ], total

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to list template assets",
                internal_details=str(e),
            ) from e