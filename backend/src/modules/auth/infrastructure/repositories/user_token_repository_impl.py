from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.user_token_entity import UserTokenEntity
from src.modules.auth.domain.repositories.user_token_repository import IUserTokenRepository
from src.shared.infrastructure.repository.base_repository import BaseRepository


class UserTokenRepository(BaseRepository[UserTokenEntity], IUserTokenRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, "sys_auth_user_tokens")

    def to_row(self, entity: UserTokenEntity) -> dict:
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "user_id": entity.user_id,
            "type": entity.type,
            "token_hash": entity.token_hash,
            "expires_at": entity.expires_at,
            "used_at": entity.used_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> UserTokenEntity:
        return UserTokenEntity(
            id=row.get("id"),
            uuid=row.get("uuid", ""),
            user_id=row.get("user_id", 0),
            type=row.get("type", ""),
            token_hash=row.get("token_hash", ""),
            expires_at=row.get("expires_at") or datetime.now(UTC) + timedelta(hours=1),
            used_at=row.get("used_at"),
            created_at=row.get("created_at") or datetime.now(UTC),
            updated_at=row.get("updated_at"),
        )
