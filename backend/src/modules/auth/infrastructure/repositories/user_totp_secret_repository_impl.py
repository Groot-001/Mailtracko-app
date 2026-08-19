from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.user_totp_secret_entity import UserTotpSecretEntity
from src.modules.auth.domain.repositories.user_totp_secret_repository import IUserTotpSecretRepository
from src.shared.infrastructure.repository.base_repository import BaseRepository


class UserTotpSecretRepositoryImpl(BaseRepository[UserTotpSecretEntity], IUserTotpSecretRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, "auth_user_totp_secrets")

    def to_row(self, entity: UserTotpSecretEntity) -> dict:
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "user_id": entity.user_id,
            "secret": entity.secret,
            "enabled": entity.enabled,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> UserTotpSecretEntity:
        return UserTotpSecretEntity(
            id=row.get("id"),
            uuid=row.get("uuid", ""),
            user_id=row.get("user_id", 0),
            secret=row.get("secret", ""),
            enabled=row.get("enabled", False),
            created_at=row.get("created_at") or datetime.now(UTC),
            updated_at=row.get("updated_at"),
        )
