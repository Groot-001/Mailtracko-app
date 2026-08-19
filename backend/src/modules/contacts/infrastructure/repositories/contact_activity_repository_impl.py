import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contacts.domain.entities.contact_activity_entity import (
    ContactActivityEntity,
)
from src.modules.contacts.domain.repositories.contact_activity_repository import (
    IContactActivityRepository,
)
from src.shared.infrastructure.repository.base_repository import BaseRepository


class ContactActivityRepositoryImpl(
    BaseRepository[ContactActivityEntity], IContactActivityRepository
):
    """PostgreSQL implementation of IContactActivityRepository using raw SQL."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, table_name="contact_activities")

    def to_row(self, entity: ContactActivityEntity) -> dict:
        """Convert entity to a flat dict for SQL insertion."""
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "contact_id": entity.contact_id,
            "organization_id": entity.organization_id,
            "activity_type": entity.activity_type,
            "description": entity.description,
            "metadata": (
                json.dumps(entity.metadata)
                if isinstance(entity.metadata, (dict, list))
                else entity.metadata
            ),
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> ContactActivityEntity:
        """Convert a flat DB row back into a domain entity."""
        metadata = row.get("metadata")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                pass
        return ContactActivityEntity(
            id=row.get("id"),
            uuid=row.get("uuid"),
            contact_id=row.get("contact_id"),
            organization_id=row.get("organization_id"),
            activity_type=row.get("activity_type"),
            description=row.get("description"),
            metadata=metadata,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    async def list_by_contact(
        self,
        contact_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ContactActivityEntity], int]:
        """Paginated timeline for a specific contact (newest first)."""
        count_sql = text(
            "SELECT COUNT(*) FROM contact_activities WHERE contact_id = :cid"
        )
        count_result = await self.session.execute(count_sql, {"cid": contact_id})
        total = count_result.scalar() or 0
        sql = text(
            "SELECT * FROM contact_activities WHERE contact_id = :cid "
            "ORDER BY created_at DESC LIMIT :lim OFFSET :off",
        )
        result = await self.session.execute(
            sql, {"cid": contact_id, "lim": limit, "off": offset}
        )
        rows = result.mappings().all()
        return [self.to_entity(dict(row)) for row in rows], total
