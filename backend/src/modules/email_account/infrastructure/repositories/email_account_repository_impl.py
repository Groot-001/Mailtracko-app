import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.email_account.domain.entities.email_account_entity import EmailAccountEntity
from src.modules.email_account.domain.repositories.email_account_repository import IEmailAccountRepository
from src.shared.infrastructure.repository.base_repository import BaseRepository


class EmailAccountRepositoryImpl(BaseRepository[EmailAccountEntity], IEmailAccountRepository):

    auto_filter_deleted = True

    def __init__(self, session: AsyncSession):
        super().__init__(session, table_name="email_accounts")

    def to_row(self, entity: EmailAccountEntity) -> dict:
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "organization_id": entity.organization_id,
            "provider": entity.provider,
            "email": entity.email,
            "sender_name": entity.sender_name,
            "status": entity.status,
            "smtp_config_id": entity.smtp_config_id,
            "oauth_config_id": entity.oauth_config_id,
            "health_status": entity.health_status,
            "daily_sent_count": entity.daily_sent_count,
            "last_sent_date": entity.last_sent_date,
            "sending_limit": entity.sending_limit,
            "reply_to": entity.reply_to,
            "signature": entity.signature,
            "last_used_at": entity.last_used_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "created_by_id": entity.created_by_id,
            "updated_by_id": entity.updated_by_id,
            "deleted_at": entity.deleted_at,
            "health_score": entity.health_score,
            "health_details": json.dumps(entity.health_details) if entity.health_details else None,
        }

    def to_entity(self, row: dict) -> EmailAccountEntity:
        return EmailAccountEntity(
            id=row.get("id"),
            uuid=row["uuid"],
            organization_id=row["organization_id"],
            provider=row["provider"],
            email=row["email"],
            sender_name=row.get("sender_name"),
            status=row.get("status", "pending_verification"),
            smtp_config_id=row.get("smtp_config_id"),
            oauth_config_id=row.get("oauth_config_id"),
            health_status=row.get("health_status", "unknown"),
            daily_sent_count=row.get("daily_sent_count", 0),
            last_sent_date=row.get("last_sent_date"),
            sending_limit=row.get("sending_limit", 100),
            reply_to=row.get("reply_to"),
            signature=row.get("signature"),
            last_used_at=row.get("last_used_at"),
            created_at=row["created_at"],
            updated_at=row.get("updated_at"),
            created_by_id=row.get("created_by_id"),
            updated_by_id=row.get("updated_by_id"),
            deleted_at=row.get("deleted_at"),
            health_score=row.get("health_score"),
            health_details=row.get("health_details"),
        )

    async def list_by_organization(
        self, organization_id: int, limit: int = 50, offset: int = 0,
    ) -> tuple[list[EmailAccountEntity], int]:
        count_sql = text("SELECT COUNT(*) FROM email_accounts WHERE organization_id = :org_id AND deleted_at IS NULL")
        count_result = await self.session.execute(count_sql, {"org_id": organization_id})
        total = count_result.scalar() or 0
        sql = text(
            "SELECT * FROM email_accounts WHERE organization_id = :org_id AND deleted_at IS NULL "
            "ORDER BY created_at DESC LIMIT :lim OFFSET :off"
        )
        result = await self.session.execute(sql, {"org_id": organization_id, "lim": limit, "off": offset})
        rows = result.mappings().all()
        return [self.to_entity(dict(row)) for row in rows], total

    async def get_by_email_and_organization(
        self, email: str, organization_id: int,
    ) -> EmailAccountEntity | None:
        sql = text(
            "SELECT * FROM email_accounts WHERE email = :email AND organization_id = :org_id "
            "AND deleted_at IS NULL LIMIT 1"
        )
        result = await self.session.execute(sql, {"email": email, "org_id": organization_id})
        row = result.mappings().one_or_none()
        return self.to_entity(dict(row)) if row else None

    async def get_by_email_and_organization_including_deleted(
        self, email: str, organization_id: int,
    ) -> EmailAccountEntity | None:
        sql = text(
            "SELECT * FROM email_accounts WHERE email = :email AND organization_id = :org_id "
            "LIMIT 1"
        )
        result = await self.session.execute(sql, {"email": email, "org_id": organization_id})
        row = result.mappings().one_or_none()
        return self.to_entity(dict(row)) if row else None

    async def list_active_by_organization(
        self, organization_id: int,
    ) -> list[EmailAccountEntity]:
        sql = text(
            "SELECT * FROM email_accounts WHERE organization_id = :org_id "
            "AND status = 'active' AND deleted_at IS NULL"
        )
        result = await self.session.execute(sql, {"org_id": organization_id})
        rows = result.mappings().all()
        return [self.to_entity(dict(row)) for row in rows]

    async def list_expired_pending(
        self, expiry_minutes: int = 1440,
    ) -> list[EmailAccountEntity]:
        sql = text(
            "SELECT ea.* FROM email_accounts ea "
            "JOIN email_smtp_configs esc ON ea.smtp_config_id = esc.id "
            "WHERE ea.status = 'pending_verification' AND ea.deleted_at IS NULL "
            "AND esc.verification_sent_at IS NOT NULL "
            "AND EXTRACT(EPOCH FROM (NOW() - esc.verification_sent_at)) / 60 > :expiry"
        )
        result = await self.session.execute(sql, {"expiry": expiry_minutes})
        rows = result.mappings().all()
        return [self.to_entity(dict(row)) for row in rows]

    async def count_by_organization(self, organization_id: int) -> int:
        sql = text("SELECT COUNT(*) FROM email_accounts WHERE organization_id = :org_id AND deleted_at IS NULL")
        result = await self.session.execute(sql, {"org_id": organization_id})
        return result.scalar() or 0