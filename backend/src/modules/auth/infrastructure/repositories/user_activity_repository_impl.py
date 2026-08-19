import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.user_activity_entity import UserActivityEntity
from src.modules.auth.domain.repositories.user_activity_repository import IUserActivityRepository
from src.shared.infrastructure.repository.base_repository import BaseRepository


class UserActivityRepositoryImpl(BaseRepository[UserActivityEntity], IUserActivityRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, table_name="auth_user_activities")

    def to_row(self, entity: UserActivityEntity) -> dict:
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "user_id": entity.user_id,
            "activity_type": entity.activity_type,
            "description": entity.description,
            "metadata": (
                json.dumps(entity.metadata)
                if isinstance(entity.metadata, (dict, list))
                else entity.metadata
            ),
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> UserActivityEntity:
        metadata = row.get("metadata")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                pass
        return UserActivityEntity(
            id=row.get("id"),
            uuid=row.get("uuid"),
            user_id=row.get("user_id"),
            activity_type=row.get("activity_type"),
            description=row.get("description"),
            metadata=metadata,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    async def list_by_user(
        self, user_id: int, limit: int = 50, offset: int = 0,
    ) -> tuple[list[UserActivityEntity], int]:
        count_sql = text("SELECT COUNT(*) FROM auth_user_activities WHERE user_id = :uid")
        count_result = await self.session.execute(count_sql, {"uid": user_id})
        total = count_result.scalar() or 0
        sql = text(
            "SELECT * FROM auth_user_activities WHERE user_id = :uid "
            "ORDER BY created_at DESC LIMIT :lim OFFSET :off",
        )
        result = await self.session.execute(sql, {"uid": user_id, "lim": limit, "off": offset})
        rows = result.mappings().all()
        return [self.to_entity(dict(row)) for row in rows], total
