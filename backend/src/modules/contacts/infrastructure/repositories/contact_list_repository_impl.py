import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contacts.domain.entities.contact_list_entity import ContactListEntity
from src.modules.contacts.domain.repositories.contact_list_repository import (
    IContactListRepository,
)
from src.shared.infrastructure.repository.base_repository import BaseRepository


class ContactListRepositoryImpl(
    BaseRepository[ContactListEntity], IContactListRepository
):
    """PostgreSQL implementation of IContactListRepository using raw SQL."""

    auto_filter_deleted = True

    def __init__(self, session: AsyncSession):
        super().__init__(session, table_name="contact_lists")

    def to_row(self, entity: ContactListEntity) -> dict:
        """Convert entity to a flat dict for SQL insertion."""
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "organization_id": entity.organization_id,
            "name": entity.name,
            "description": entity.description,
            "field_definitions": (
                json.dumps(entity.field_definitions)
                if isinstance(entity.field_definitions, (dict, list))
                else entity.field_definitions
            ),
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "created_by_id": entity.created_by_id,
            "updated_by_id": entity.updated_by_id,
            "deleted_at": entity.deleted_at,
        }

    def to_entity(self, row: dict) -> ContactListEntity:
        """Convert a flat DB row back into a domain entity."""
        field_defs = row.get("field_definitions")
        if isinstance(field_defs, str):
            try:
                field_defs = json.loads(field_defs)
            except Exception:
                pass
        return ContactListEntity(
            id=row.get("id"),
            uuid=row.get("uuid"),
            organization_id=row.get("organization_id"),
            name=row.get("name"),
            description=row.get("description"),
            field_definitions=field_defs,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            created_by_id=row.get("created_by_id"),
            updated_by_id=row.get("updated_by_id"),
            deleted_at=row.get("deleted_at"),
        )

    async def list_by_organization(
        self,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ContactListEntity], int]:
        """Paginated list of all lists belonging to an organization."""
        count_sql = text(
            "SELECT COUNT(*) FROM contact_lists WHERE organization_id = :org_id AND deleted_at IS NULL"
        )
        count_result = await self.session.execute(
            count_sql, {"org_id": organization_id}
        )
        total = count_result.scalar() or 0
        sql = text(
            "SELECT * FROM contact_lists WHERE organization_id = :org_id AND deleted_at IS NULL "
            "ORDER BY created_at DESC LIMIT :lim OFFSET :off"
        )
        result = await self.session.execute(
            sql, {"org_id": organization_id, "lim": limit, "off": offset}
        )
        rows = result.mappings().all()
        return [self.to_entity(dict(row)) for row in rows], total

    async def list_summaries_by_organization(
        self,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Return list metadata plus contact counters without N+1 queries."""
        count_sql = text(
            "SELECT COUNT(*) FROM contact_lists "
            "WHERE organization_id = :org_id AND deleted_at IS NULL"
        )
        count_result = await self.session.execute(count_sql, {"org_id": organization_id})
        total = int(count_result.scalar() or 0)

        sql = text(
            """
            SELECT
                cl.uuid, cl.name, cl.description, cl.field_definitions,
                cl.created_at, cl.updated_at,
                COUNT(c.id) AS contact_count,
                COUNT(c.id) FILTER (
                    WHERE c.verification_status = 'valid'
                ) AS verified_count
            FROM contact_lists cl
            LEFT JOIN contact_contacts c ON c.contact_list_id = cl.id
            WHERE cl.organization_id = :org_id AND cl.deleted_at IS NULL
            GROUP BY cl.id
            ORDER BY cl.created_at DESC
            LIMIT :lim OFFSET :off
            """
        )
        result = await self.session.execute(
            sql, {"org_id": organization_id, "lim": limit, "off": offset}
        )
        items: list[dict] = []
        for row in result.mappings().all():
            item = dict(row)
            field_defs = item.get("field_definitions")
            if isinstance(field_defs, str):
                try:
                    item["field_definitions"] = json.loads(field_defs)
                except Exception:
                    pass
            item["contact_count"] = int(item.get("contact_count") or 0)
            item["verified_count"] = int(item.get("verified_count") or 0)
            items.append(item)
        return items, total

    async def count_by_organization(self, organization_id: int) -> int:
        """Count all lists in an organization."""
        sql = text(
            "SELECT COUNT(*) FROM contact_lists WHERE organization_id = :org_id AND deleted_at IS NULL"
        )
        result = await self.session.execute(sql, {"org_id": organization_id})
        return result.scalar() or 0


