from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.user_entity import UserEntity
from src.modules.auth.domain.repositories.user_repository import IUserRepository
from src.shared.infrastructure.repository.base_repository import BaseRepository


class UserRepository(BaseRepository[UserEntity], IUserRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, "sys_auth_users")

    def to_row(self, entity: UserEntity) -> dict:
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "full_name": entity.full_name,
            "email": entity.email,
            "profile_image": entity.profile_image,
            "timezone": entity.timezone,
            "phone": entity.phone,
            "country_code": entity.country_code,
            "location": entity.location,
            "theme": entity.theme,
            "is_active": entity.is_active,
            "last_login_at": entity.last_login_at,
            "scheduled_deletion_at": entity.scheduled_deletion_at,
            "email_verified_at": entity.email_verified_at,
            "created_by_id": entity.created_by_id,
            "updated_by_id": entity.updated_by_id,
            "deleted_at": entity.deleted_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> UserEntity:
        return UserEntity(
            id=row.get("id"),
            uuid=row.get("uuid", ""),
            full_name=row.get("full_name", ""),
            email=row.get("email", ""),
            profile_image=row.get("profile_image"),
            timezone=row.get("timezone"),
            phone=row.get("phone"),
            country_code=row.get("country_code"),
            location=row.get("location"),
            theme=row.get("theme", "light"),
            is_active=row.get("is_active", True),
            last_login_at=row.get("last_login_at"),
            scheduled_deletion_at=row.get("scheduled_deletion_at"),
            email_verified_at=row.get("email_verified_at"),
            created_by_id=row.get("created_by_id"),
            updated_by_id=row.get("updated_by_id"),
            deleted_at=row.get("deleted_at"),
            created_at=row.get("created_at") or datetime.now(UTC),
            updated_at=row.get("updated_at"),
        )
