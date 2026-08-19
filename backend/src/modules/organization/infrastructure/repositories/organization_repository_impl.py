from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from src.modules.organization.domain.entities.organization_entity import (
    OrganizationEntity,
)
from src.modules.organization.domain.repositories.organization_repository import (
    IOrganizationRepository,
)
from src.modules.organization.infrastructure.models.organization_model import (
    OrganizationModel,
)
from src.shared.exceptions.base_exceptions import ServerError
from src.shared.infrastructure.repository.base_repository import BaseRepository


class OrganizationRepositoryImpl(
    BaseRepository[OrganizationEntity], IOrganizationRepository
):
    """
    SQLAlchemy implementation of the organization repository.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.table_name = OrganizationModel.__tablename__
        super().__init__(session, self.table_name)

    def to_row(self, entity: OrganizationEntity) -> dict:
        """
        Convert an OrganizationEntity to a database row.
        """
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "name": entity.name,
            "website_url": entity.website_url,
            "org_size": entity.org_size,
            "monthly_email_volume": entity.monthly_email_volume,
            "domain_email": entity.domain_email,
            "org_logo": entity.org_logo,
            "description": entity.description,
            "industry_sector": entity.industry_sector,
            "source": entity.source,
            "theme": entity.theme,
            "timezone": entity.timezone,
            "status": entity.status,
            "owner_id": entity.owner_id,
            "deletion_requested_at": entity.deletion_requested_at,
            "deletion_requested_by_id": entity.deletion_requested_by_id,
            "scheduled_deletion_at": entity.scheduled_deletion_at,
            "created_by_id": entity.created_by_id,
            "updated_by_id": entity.updated_by_id,
            "deleted_at": entity.deleted_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> OrganizationEntity:
        """
        Convert a database row to OrganizationEntity.
        """
        return OrganizationEntity(
            id=row["id"],
            uuid=row["uuid"],
            name=row["name"],
            website_url=row.get("website_url"),
            org_size=row.get("org_size"),
            monthly_email_volume=row.get("monthly_email_volume"),
            domain_email=row.get("domain_email"),
            org_logo=row.get("org_logo"),
            description=row.get("description"),
            industry_sector=row.get("industry_sector"),
            source=row.get("source"),
            theme=row.get("theme") or "light",
            timezone=row.get("timezone") or "UTC",
            status=row.get("status") or "active",
            owner_id=row["owner_id"],
            deletion_requested_at=row.get("deletion_requested_at"),
            deletion_requested_by_id=row.get("deletion_requested_by_id"),
            scheduled_deletion_at=row.get("scheduled_deletion_at"),
            created_by_id=row.get("created_by_id"),
            updated_by_id=row.get("updated_by_id"),
            deleted_at=row.get("deleted_at"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_active_by_owner_id(
        self,
        owner_id: int,
    ) -> OrganizationEntity | None:
        """
        Retrieves active organization owned by the given user.
        """
        sql = text(
            f"SELECT * FROM {self.table_name} "
            "WHERE owner_id = :owner_id "
            "AND status = 'active' "
            "AND deleted_at IS NULL "
            "LIMIT 1"
        )

        try:
            result = await self.session.execute(sql, {"owner_id": owner_id})
            row = result.mappings().one_or_none()
            return self.to_entity(dict(row)) if row else None

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to fetch active organization by owner ID",
                internal_details=str(e),
            ) from e