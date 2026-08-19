
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.email_account.domain.entities.oauth_config_entity import OauthConfigEntity
from src.modules.email_account.domain.repositories.oauth_config_repository import IOauthConfigRepository
from src.shared.infrastructure.repository.base_repository import BaseRepository


class OauthConfigRepositoryImpl(BaseRepository[OauthConfigEntity], IOauthConfigRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session, table_name="email_oauth_configs")

    def to_row(self, entity: OauthConfigEntity) -> dict:
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "encrypted_refresh_token": entity.encrypted_refresh_token,
            "organization_id": entity.organization_id,
            "purpose": entity.purpose,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> OauthConfigEntity:
        return OauthConfigEntity(
            id=row.get("id"),
            uuid=row["uuid"],
            encrypted_refresh_token=row["encrypted_refresh_token"],
            organization_id=row.get("organization_id"),
            purpose=row.get("purpose"),
            created_at=row["created_at"],
            updated_at=row.get("updated_at"),
        )

    async def get_by_context(self, organization_id: int, purpose: str) -> OauthConfigEntity | None:
        return await self.get_by(organization_id=organization_id, purpose=purpose)
