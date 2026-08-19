from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.user_totp_recovery_code_entity import UserTotpRecoveryCodeEntity
from src.modules.auth.domain.repositories.user_totp_recovery_code_repository import (
    IUserTotpRecoveryCodeRepository,
)
from src.shared.infrastructure.repository.base_repository import BaseRepository


class UserTotpRecoveryCodeRepositoryImpl(BaseRepository[UserTotpRecoveryCodeEntity], IUserTotpRecoveryCodeRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, "auth_user_totp_recovery_codes")

    def to_row(self, entity: UserTotpRecoveryCodeEntity) -> dict:
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "user_id": entity.user_id,
            "code_hash": entity.code_hash,
            "used_at": entity.used_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> UserTotpRecoveryCodeEntity:
        return UserTotpRecoveryCodeEntity(
            id=row.get("id"),
            uuid=row.get("uuid", ""),
            user_id=row.get("user_id", 0),
            code_hash=row.get("code_hash", ""),
            used_at=row.get("used_at"),
            created_at=row.get("created_at") or datetime.now(UTC),
            updated_at=row.get("updated_at"),
        )

    async def mark_used(self, entity_id: int) -> None:
        now = datetime.now(UTC)
        sql = text(f"UPDATE {self.table_name} SET used_at = :used_at, updated_at = :updated_at WHERE id = :id")
        await self.session.execute(
            sql,
            {"used_at": now, "updated_at": now, "id": entity_id},
        )
