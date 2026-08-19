from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from src.modules.organization.domain.entities.organization_activity_entity import (
    OrganizationActivityEntity,
)
from src.modules.organization.domain.repositories.organization_activity_repository import (
    IOrganizationActivityRepository,
)
from src.modules.organization.infrastructure.models.organization_activity_model import (
    OrganizationActivityModel,
)
from src.shared.exceptions.base_exceptions import ServerError
from src.shared.infrastructure.repository.base_repository import BaseRepository


class OrganizationActivityRepositoryImpl(
    BaseRepository[OrganizationActivityEntity],
    IOrganizationActivityRepository,
):
    """
    SQLAlchemy implementation of organization activity repository.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.table_name = OrganizationActivityModel.__tablename__
        super().__init__(session, self.table_name)

    def to_row(self, entity: OrganizationActivityEntity) -> dict:
        """
        Convert OrganizationActivityEntity to database row.
        """
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "organization_id": entity.organization_id,
            "activity_type": entity.activity_type,
            "title": entity.title,
            "actor_user_id": entity.actor_user_id,
            "target_user_id": entity.target_user_id,
            "target_email": entity.target_email,
            "created_by_id": entity.created_by_id,
            "updated_by_id": entity.updated_by_id,
            "deleted_at": entity.deleted_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> OrganizationActivityEntity:
        """
        Convert database row to OrganizationActivityEntity.
        """
        return OrganizationActivityEntity(
            id=row["id"],
            uuid=row["uuid"],
            organization_id=row["organization_id"],
            activity_type=row["activity_type"],
            title=row["title"],
            actor_user_id=row.get("actor_user_id"),
            target_user_id=row.get("target_user_id"),
            target_email=row.get("target_email"),
            created_by_id=row.get("created_by_id"),
            updated_by_id=row.get("updated_by_id"),
            deleted_at=row.get("deleted_at"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def list_by_organization_id(
        self,
        organization_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> list[OrganizationActivityEntity]:
        """
        Lists recent activities for an organization.
        """
        sql = text(
            f"SELECT * FROM {self.table_name} "
            "WHERE organization_id = :organization_id "
            "AND deleted_at IS NULL "
            "ORDER BY created_at DESC "
            "LIMIT :limit OFFSET :offset"
        )

        try:
            result = await self.session.execute(
                sql,
                {
                    "organization_id": organization_id,
                    "limit": limit,
                    "offset": offset,
                },
            )
            rows = result.mappings().all()

            return [self.to_entity(dict(row)) for row in rows]

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to list organization activities",
                internal_details=str(e),
            ) from e

    async def count_by_organization_id(
        self,
        organization_id: int,
    ) -> int:
        """
        Counts recent activities for an organization.
        """
        sql = text(
            f"SELECT COUNT(*) FROM {self.table_name} "
            "WHERE organization_id = :organization_id "
            "AND deleted_at IS NULL"
        )

        try:
            result = await self.session.execute(
                sql,
                {"organization_id": organization_id},
            )

            return int(result.scalar() or 0)

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to count organization activities",
                internal_details=str(e),
            ) from e