import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contacts.domain.entities.contact_import_log_entity import (
    ContactImportLogEntity,
)
from src.modules.contacts.domain.repositories.contact_import_log_repository import (
    IContactImportLogRepository,
)
from src.shared.infrastructure.repository.base_repository import BaseRepository


class ContactImportLogRepositoryImpl(
    BaseRepository[ContactImportLogEntity], IContactImportLogRepository
):
    """PostgreSQL implementation of IContactImportLogRepository using raw SQL."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, table_name="contact_import_logs")

    def to_row(self, entity: ContactImportLogEntity) -> dict:
        """Convert entity to a flat dict for SQL insertion."""
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "organization_id": entity.organization_id,
            "contact_list_id": entity.contact_list_id,
            "filename": entity.filename,
            "column_mapping": (
                json.dumps(entity.column_mapping)
                if isinstance(entity.column_mapping, (dict, list))
                else entity.column_mapping
            ),
            "total_rows": entity.total_rows,
            "success_count": entity.success_count,
            "error_count": entity.error_count,
            "errors": (
                json.dumps(entity.errors)
                if isinstance(entity.errors, (dict, list))
                else entity.errors
            ),
            "status": entity.status,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "created_by_id": entity.created_by_id,
            "updated_by_id": entity.updated_by_id,
        }

    def to_entity(self, row: dict) -> ContactImportLogEntity:
        """Convert a flat DB row back into a domain entity."""
        col_map = row.get("column_mapping")
        if isinstance(col_map, str):
            try:
                col_map = json.loads(col_map)
            except Exception:
                pass
        errs = row.get("errors")
        if isinstance(errs, str):
            try:
                errs = json.loads(errs)
            except Exception:
                pass
        return ContactImportLogEntity(
            id=row.get("id"),
            uuid=row.get("uuid"),
            organization_id=row.get("organization_id"),
            contact_list_id=row.get("contact_list_id"),
            filename=row.get("filename"),
            column_mapping=col_map,
            total_rows=row.get("total_rows", 0),
            success_count=row.get("success_count", 0),
            error_count=row.get("error_count", 0),
            errors=errs,
            status=row.get("status", "pending"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            created_by_id=row.get("created_by_id"),
            updated_by_id=row.get("updated_by_id"),
        )

    async def list_by_organization(
        self,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ContactImportLogEntity], int]:
        """Paginated list of all import logs for an organization."""
        count_sql = text(
            "SELECT COUNT(*) FROM contact_import_logs WHERE organization_id = :org_id"
        )
        count_result = await self.session.execute(
            count_sql, {"org_id": organization_id}
        )
        total = count_result.scalar() or 0
        sql = text(
            "SELECT * FROM contact_import_logs WHERE organization_id = :org_id "
            "ORDER BY created_at DESC LIMIT :lim OFFSET :off",
        )
        result = await self.session.execute(
            sql, {"org_id": organization_id, "lim": limit, "off": offset}
        )
        rows = result.mappings().all()
        return [self.to_entity(dict(row)) for row in rows], total

    async def list_by_list(
        self,
        contact_list_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ContactImportLogEntity], int]:
        """Paginated list of import logs targeting a specific list."""
        count_sql = text(
            "SELECT COUNT(*) FROM contact_import_logs WHERE contact_list_id = :lid"
        )
        count_result = await self.session.execute(count_sql, {"lid": contact_list_id})
        total = count_result.scalar() or 0
        sql = text(
            "SELECT * FROM contact_import_logs WHERE contact_list_id = :lid "
            "ORDER BY created_at DESC LIMIT :lim OFFSET :off",
        )
        result = await self.session.execute(
            sql, {"lid": contact_list_id, "lim": limit, "off": offset}
        )
        rows = result.mappings().all()
        return [self.to_entity(dict(row)) for row in rows], total
