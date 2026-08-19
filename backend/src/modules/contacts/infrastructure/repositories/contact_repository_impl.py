import json

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contacts.domain.entities.contact_entity import ContactEntity
from src.modules.contacts.domain.repositories.contact_repository import (
    IContactRepository,
)
from src.shared.infrastructure.repository.base_repository import BaseRepository


class ContactRepositoryImpl(BaseRepository[ContactEntity], IContactRepository):
    """PostgreSQL implementation of IContactRepository using raw SQL."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, table_name="contact_contacts")

    def to_row(self, entity: ContactEntity) -> dict:
        """Convert entity to a flat dict for SQL insertion."""
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "organization_id": entity.organization_id,
            "contact_list_id": entity.contact_list_id,
            "email": entity.email,
            "metadata": (
                json.dumps(entity.metadata)
                if isinstance(entity.metadata, (dict, list))
                else entity.metadata
            ),
            "subscribed": entity.subscribed,
            "unsubscribed_at": entity.unsubscribed_at,
            "last_contacted_at": entity.last_contacted_at,
            "status": entity.status,
            "verification_status": entity.verification_status,
            "verification_sub_status": entity.verification_sub_status,
            "verification_score": entity.verification_score,
            "verification_details": (
                json.dumps(entity.verification_details)
                if isinstance(entity.verification_details, (dict, list))
                else entity.verification_details
            ),
            "verified_at": entity.verified_at,
            "bounce_risk": entity.bounce_risk,
            "last_bounced_at": entity.last_bounced_at,
            "archived_at": entity.archived_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> ContactEntity:
        """Convert a flat DB row back into a domain entity."""
        metadata = row.get("metadata")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                pass
        verification_details = row.get("verification_details")
        if isinstance(verification_details, str):
            try:
                verification_details = json.loads(verification_details)
            except Exception:
                pass
        return ContactEntity(
            id=row.get("id"),
            uuid=row.get("uuid"),
            organization_id=row.get("organization_id"),
            contact_list_id=row.get("contact_list_id"),
            email=row.get("email"),
            metadata=metadata,
            subscribed=row.get("subscribed", True),
            unsubscribed_at=row.get("unsubscribed_at"),
            last_contacted_at=row.get("last_contacted_at"),
            status=row.get("status", "active"),
            verification_status=row.get("verification_status", "unverified"),
            verification_sub_status=row.get("verification_sub_status"),
            verification_score=row.get("verification_score"),
            verification_details=verification_details,
            verified_at=row.get("verified_at"),
            bounce_risk=row.get("bounce_risk"),
            last_bounced_at=row.get("last_bounced_at"),
            archived_at=row.get("archived_at"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    async def get_by_email_and_list(
        self,
        email: str,
        contact_list_id: int,
    ) -> ContactEntity | None:
        """Find a contact by email within a given list (used for duplicate check)."""
        sql = text(
            "SELECT * FROM contact_contacts WHERE email = :email AND contact_list_id = :lid LIMIT 1",
        )
        result = await self.session.execute(
            sql, {"email": email, "lid": contact_list_id}
        )
        row = result.mappings().one_or_none()
        return self.to_entity(dict(row)) if row else None

    async def list_by_list(
        self,
        contact_list_id: int,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        subscribed: bool | None = None,
        company: str | None = None,
        tag: str | None = None,
        status: str | None = None,
        verification_status: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[ContactEntity], int]:
        """
        Paginated, filterable, sortable query of contacts within a list.

        Supports ILIKE search on email/name/company, filtering by company
        and subscription status, and sorting by allowed columns.
        """
        allowed_sorts = {"created_at", "email", "status", "verification_score"}
        if sort_by not in allowed_sorts:
            sort_by = "created_at"
        sort_dir = "DESC" if sort_order.lower() == "desc" else "ASC"

        conditions = [
            "c.contact_list_id = :lid",
            "NOT EXISTS (SELECT 1 FROM contact_lists l WHERE l.id = c.contact_list_id AND l.deleted_at IS NOT NULL)",
        ]
        params: dict = {"lid": contact_list_id, "lim": limit, "off": offset}

        if search:
            conditions.append(
                "(c.email ILIKE :search OR COALESCE(c.metadata->>'name', '') ILIKE :search "
                "OR COALESCE(c.metadata->>'first_name', '') ILIKE :search "
                "OR COALESCE(c.metadata->>'last_name', '') ILIKE :search "
                "OR COALESCE(c.metadata->>'company', '') ILIKE :search "
                "OR COALESCE(c.metadata->>'tags', '') ILIKE :search)"
            )
            params["search"] = f"%{search}%"

        if subscribed is not None:
            conditions.append("c.subscribed = :subscribed")
            params["subscribed"] = subscribed

        if company:
            conditions.append("COALESCE(c.metadata->>'company', '') ILIKE :company")
            params["company"] = f"%{company.strip()}%"

        if tag:
            conditions.append("COALESCE(c.metadata->>'tags', '') ILIKE :tag")
            params["tag"] = f"%{tag.strip()}%"

        if status:
            conditions.append("c.status = :status")
            params["status"] = status

        if verification_status:
            conditions.append("c.verification_status = :verification_status")
            params["verification_status"] = verification_status

        where_clause = " AND ".join(conditions)

        count_sql = text(
            f"SELECT COUNT(*) FROM contact_contacts c WHERE {where_clause}"
        )
        count_result = await self.session.execute(count_sql, params)
        total = count_result.scalar() or 0

        data_sql = text(
            f"SELECT c.* FROM contact_contacts c WHERE {where_clause} "
            f"ORDER BY c.{sort_by} {sort_dir} LIMIT :lim OFFSET :off",
        )
        result = await self.session.execute(data_sql, params)
        rows = result.mappings().all()
        return [self.to_entity(dict(row)) for row in rows], total

    async def count_by_list(self, contact_list_id: int) -> int:
        """Count total contacts in a list (excludes contacts of soft-deleted parent lists)."""
        sql = text(
            "SELECT COUNT(*) FROM contact_contacts c WHERE c.contact_list_id = :lid "
            "AND NOT EXISTS (SELECT 1 FROM contact_lists l WHERE l.id = c.contact_list_id AND l.deleted_at IS NOT NULL)"
        )
        result = await self.session.execute(sql, {"lid": contact_list_id})
        return result.scalar() or 0

    async def list_all_by_list(self, contact_list_id: int) -> list[ContactEntity]:
        sql = text(
            "SELECT * FROM contact_contacts WHERE contact_list_id = :lid "
            "AND NOT EXISTS (SELECT 1 FROM contact_lists l WHERE l.id = contact_contacts.contact_list_id AND l.deleted_at IS NOT NULL)"
        )
        result = await self.session.execute(sql, {"lid": contact_list_id})
        rows = result.mappings().all()
        return [self.to_entity(dict(row)) for row in rows]

    async def get_existing_by_emails(
        self,
        emails: list[str],
        contact_list_id: int,
    ) -> list[ContactEntity]:
        """Return existing contacts matching the given emails within a list."""
        if not emails:
            return []
        sql = text(
            "SELECT * FROM contact_contacts WHERE contact_list_id = :lid AND email IN :emails"
        ).bindparams(bindparam("emails", expanding=True))
        result = await self.session.execute(
            sql, {"lid": contact_list_id, "emails": emails}
        )
        rows = result.mappings().all()
        return [self.to_entity(dict(row)) for row in rows]

    async def bulk_upsert(
        self,
        entities: list[ContactEntity],
    ) -> tuple[list[ContactEntity], int]:
        """
        Bulk insert or update contacts within a list.

        Matches existing contacts by email within the same list.
        Existing contacts have their fields updated (non-null values win).
        Returns (all_contacts, number_updated).
        """
        if not entities:
            return [], 0

        contact_list_id = entities[0].contact_list_id
        if any(e.contact_list_id != contact_list_id for e in entities):
            raise ValueError("All entities must belong to the same contact list")

        emails = list({e.email for e in entities})

        sql = text(
            "SELECT * FROM contact_contacts WHERE contact_list_id = :lid AND email IN :emails FOR UPDATE"
        ).bindparams(bindparam("emails", expanding=True))
        result = await self.session.execute(
            sql, {"lid": contact_list_id, "emails": emails}
        )
        rows = result.mappings().all()
        existing_map: dict[str, ContactEntity] = {
            row["email"]: self.to_entity(dict(row)) for row in rows
        }

        created = []
        updated_count = 0
        for entity in entities:
            existing = existing_map.get(entity.email)
            if existing:
                if entity.metadata:
                    if existing.metadata:
                        existing.metadata.update(entity.metadata)
                    else:
                        existing.metadata = entity.metadata
                existing.mark_updated()
                updated = await self.update(existing)
                created.append(updated)
                existing_map[entity.email] = updated
                updated_count += 1
            else:
                new_entity = await self.add(entity)
                created.append(new_entity)
                existing_map[entity.email] = new_entity
        return created, updated_count
