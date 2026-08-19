from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.user_account_entity import UserAccountEntity
from src.modules.auth.domain.repositories.user_account_repository import IUserAccountRepository
from src.shared.infrastructure.repository.base_repository import BaseRepository


class UserAccountRepository(BaseRepository[UserAccountEntity], IUserAccountRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, "sys_auth_user_accounts")

    def to_row(self, entity: UserAccountEntity) -> dict:
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "user_id": entity.user_id,
            "type": entity.type,
            "hashed_password": entity.hashed_password,
            "provider": entity.provider,
            "provider_account_id": entity.provider_account_id,
            "last_password_updated_at": entity.last_password_updated_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> UserAccountEntity:
        return UserAccountEntity(
            id=row.get("id"),
            uuid=row.get("uuid", ""),
            user_id=row.get("user_id", 0),
            type=row.get("type", "password"),
            hashed_password=row.get("hashed_password"),
            provider=row.get("provider"),
            provider_account_id=row.get("provider_account_id"),
            last_password_updated_at=row.get("last_password_updated_at"),
            created_at=row.get("created_at") or datetime.now(UTC),
            updated_at=row.get("updated_at"),
        )
