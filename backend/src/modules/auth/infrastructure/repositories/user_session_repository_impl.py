from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.user_session_entity import UserSessionEntity
from src.modules.auth.domain.repositories.user_session_repository import IUserSessionRepository
from src.shared.infrastructure.repository.base_repository import BaseRepository


class UserSessionRepository(BaseRepository[UserSessionEntity], IUserSessionRepository):
    """Repository for managing user session persistence in sys_auth_user_sessions."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, "sys_auth_user_sessions")

    def to_row(self, entity: UserSessionEntity) -> dict:
        """Convert a session entity to a database row dict."""
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "user_id": entity.user_id,
            "expires_at": entity.expires_at,
            "ip_address": entity.ip_address,
            "user_agent": entity.user_agent,
            "revoked_at": entity.revoked_at,
            "created_by_id": entity.created_by_id,
            "updated_by_id": entity.updated_by_id,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> UserSessionEntity:
        """Convert a database row dict to a session entity."""
        return UserSessionEntity(
            id=row.get("id"),
            uuid=row.get("uuid", ""),
            user_id=row.get("user_id", 0),
            expires_at=row.get("expires_at") or datetime.now(UTC) + timedelta(days=7),
            ip_address=row.get("ip_address"),
            user_agent=row.get("user_agent"),
            revoked_at=row.get("revoked_at"),
            created_by_id=row.get("created_by_id"),
            updated_by_id=row.get("updated_by_id"),
            created_at=row.get("created_at") or datetime.now(UTC),
            updated_at=row.get("updated_at"),
        )

    async def revoke_all_for_user(self, user_id: int) -> None:
        now = datetime.now(UTC)
        sql = text(
            "UPDATE sys_auth_user_sessions SET revoked_at = :now, updated_at = :now "
            "WHERE user_id = :user_id AND revoked_at IS NULL"
        )
        await self.session.execute(sql, {"user_id": user_id, "now": now})
        await self.session.flush()

    async def revoke_all_except(self, user_id: int, exclude_session_uuid: str) -> None:
        now = datetime.now(UTC)
        sql = text(
            "UPDATE sys_auth_user_sessions SET revoked_at = :now, updated_at = :now "
            "WHERE user_id = :user_id AND revoked_at IS NULL AND uuid != :exclude_uuid"
        )
        await self.session.execute(sql, {"user_id": user_id, "now": now, "exclude_uuid": exclude_session_uuid})
        await self.session.flush()
