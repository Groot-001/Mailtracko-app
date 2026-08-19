import json

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from src.modules.organization.domain.entities.organization_member_entity import (
    OrganizationMemberEntity,
)
from src.modules.organization.domain.repositories.organization_member_repository import (
    IOrganizationMemberRepository,
)
from src.modules.organization.infrastructure.models.organization_member_model import (
    OrganizationMemberModel,
)
from src.shared.exceptions.base_exceptions import ServerError
from src.shared.infrastructure.repository.base_repository import BaseRepository


class OrganizationMemberRepositoryImpl(
    BaseRepository[OrganizationMemberEntity], IOrganizationMemberRepository
):
    """
    SQLAlchemy implementation of the organization member repository.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.table_name = OrganizationMemberModel.__tablename__
        super().__init__(session, self.table_name)

    def to_row(self, entity: OrganizationMemberEntity) -> dict:
        """
        Convert an OrganizationMemberEntity to a database row.
        """
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "organization_id": entity.organization_id,
            "user_id": entity.user_id,
            "role_code": entity.role_code,
            "status": entity.status,
            "invited_by_id": entity.invited_by_id,
            "joined_at": entity.joined_at,
            # BaseRepository uses textual SQL, so JSON bind processing is not
            # applied automatically. Serialize explicitly for asyncpg.
            "permissions": json.dumps(entity.permissions or {}),
            "created_by_id": entity.created_by_id,
            "updated_by_id": entity.updated_by_id,
            "deleted_at": entity.deleted_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> OrganizationMemberEntity:
        """
        Convert a database row to OrganizationMemberEntity.
        """
        return OrganizationMemberEntity(
            id=row["id"],
            uuid=row["uuid"],
            organization_id=row["organization_id"],
            user_id=row["user_id"],
            role_code=row["role_code"],
            status=row["status"],
            invited_by_id=row.get("invited_by_id"),
            joined_at=row.get("joined_at"),
            permissions=self._decode_permissions(row.get("permissions")),
            created_by_id=row.get("created_by_id"),
            updated_by_id=row.get("updated_by_id"),
            deleted_at=row.get("deleted_at"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _decode_permissions(value) -> dict:
        """Normalize JSON returned by textual SQL into a permission dictionary."""
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                decoded = json.loads(value)
                return decoded if isinstance(decoded, dict) else {}
            except (TypeError, ValueError, json.JSONDecodeError):
                return {}
        return {}

    async def get_by_user_id(
        self,
        user_id: int,
    ) -> OrganizationMemberEntity | None:
        """
        Retrieves organization membership of a user.

        Since one user can belong to only one organization, this returns
        the user's single membership if it exists.
        """
        sql = text(
            f"SELECT * FROM {self.table_name} "
            "WHERE user_id = :user_id "
            "AND deleted_at IS NULL "
            "LIMIT 1"
        )

        try:
            result = await self.session.execute(sql, {"user_id": user_id})
            row = result.mappings().one_or_none()
            return self.to_entity(dict(row)) if row else None

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to fetch organization member by user ID",
                internal_details=str(e),
            ) from e

    async def get_active_by_user_id(
        self,
        user_id: int,
    ) -> OrganizationMemberEntity | None:
        """
        Retrieves active organization membership of a user.
        """
        sql = text(
            f"SELECT * FROM {self.table_name} "
            "WHERE user_id = :user_id "
            "AND status = 'active' "
            "AND deleted_at IS NULL "
            "LIMIT 1"
        )

        try:
            result = await self.session.execute(sql, {"user_id": user_id})
            row = result.mappings().one_or_none()
            return self.to_entity(dict(row)) if row else None

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to fetch active organization member",
                internal_details=str(e),
            ) from e

    async def get_by_user_and_organization(
        self,
        *,
        user_id: int,
        organization_id: int,
    ) -> OrganizationMemberEntity | None:
        """
        Retrieves organization member by user ID and organization ID.
        """
        sql = text(
            f"SELECT * FROM {self.table_name} "
            "WHERE user_id = :user_id "
            "AND organization_id = :organization_id "
            "AND deleted_at IS NULL "
            "LIMIT 1"
        )

        params = {
            "user_id": user_id,
            "organization_id": organization_id,
        }

        try:
            result = await self.session.execute(sql, params)
            row = result.mappings().one_or_none()
            return self.to_entity(dict(row)) if row else None

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to fetch organization member",
                internal_details=str(e),
            ) from e

    async def list_paginated(
        self,
        *,
        organization_id: int,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[OrganizationMemberEntity], int]:
        """
        Lists accepted organization members with pagination.
        """
        where_clauses = [
            "organization_id = :organization_id",
            "deleted_at IS NULL",
        ]

        params: dict[str, int | str] = {
            "organization_id": organization_id,
            "limit": limit,
            "offset": offset,
        }

        if status:
            where_clauses.append("status = :status")
            params["status"] = status

        where_sql = " AND ".join(where_clauses)

        list_sql = text(
            f"SELECT * FROM {self.table_name} "
            f"WHERE {where_sql} "
            "ORDER BY id DESC "
            "LIMIT :limit OFFSET :offset"
        )

        count_sql = text(
            f"SELECT COUNT(*) FROM {self.table_name} "
            f"WHERE {where_sql}"
        )

        try:
            list_result = await self.session.execute(list_sql, params)
            rows = list_result.mappings().all()

            count_result = await self.session.execute(
                count_sql,
                {
                    key: value
                    for key, value in params.items()
                    if key not in {"limit", "offset"}
                },
            )

            total = int(count_result.scalar_one())
            return [self.to_entity(dict(row)) for row in rows], total

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to list organization members",
                internal_details=str(e),
            ) from e

    async def list_paginated_with_users(
        self,
        *,
        organization_id: int,
        status: str | None = None,
        role: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Return paginated member rows enriched with authoritative user state."""
        effective_status = (
            "CASE WHEN COALESCE(u.is_active, FALSE) = FALSE "
            "THEN 'inactive' ELSE m.status END"
        )
        where_clauses = [
            "m.organization_id = :organization_id",
            "m.deleted_at IS NULL",
        ]
        params: dict[str, int | str] = {
            "organization_id": organization_id,
            "limit": limit,
            "offset": offset,
        }
        if status:
            where_clauses.append(f"({effective_status}) = :status")
            params["status"] = status
        if role:
            where_clauses.append("m.role_code = :role")
            params["role"] = role
        if search and search.strip():
            where_clauses.append(
                "(LOWER(COALESCE(u.full_name, '')) LIKE :search "
                "OR LOWER(COALESCE(u.email, '')) LIKE :search)"
            )
            params["search"] = f"%{search.strip().lower()}%"

        where_sql = " AND ".join(where_clauses)
        user_join = (
            "LEFT JOIN sys_auth_users u "
            "ON u.id = m.user_id AND u.deleted_at IS NULL "
        )
        list_sql = text(
            "SELECT m.*, "
            "u.uuid AS user_uuid, u.email AS user_email, "
            "u.full_name AS user_full_name, u.profile_image AS user_avatar, "
            "u.is_active AS user_is_active, "
            "(SELECT MAX(COALESCE(s.updated_at, s.created_at)) "
            " FROM sys_auth_user_sessions s WHERE s.user_id = m.user_id) AS last_active_at, "
            "EXISTS(SELECT 1 FROM sys_auth_user_sessions s "
            " WHERE s.user_id = m.user_id "
            " AND s.revoked_at IS NULL AND s.expires_at > NOW() "
            " AND COALESCE(s.updated_at, s.created_at) > NOW() - INTERVAL '2 minutes') AS user_is_online, "
            f"{effective_status} AS effective_status "
            f"FROM {self.table_name} m "
            + user_join
            + f"WHERE {where_sql} "
            "ORDER BY CASE WHEN m.role_code = 'owner' THEN 0 ELSE 1 END, m.id DESC "
            "LIMIT :limit OFFSET :offset"
        )
        count_sql = text(
            f"SELECT COUNT(*) FROM {self.table_name} m "
            + user_join
            + f"WHERE {where_sql}"
        )

        try:
            list_result = await self.session.execute(list_sql, params)
            rows = [dict(row) for row in list_result.mappings().all()]
            count_result = await self.session.execute(
                count_sql,
                {key: value for key, value in params.items() if key not in {"limit", "offset"}},
            )

            items: list[dict] = []
            for row in rows:
                items.append(
                    {
                        "id": row["id"],
                        "uuid": row["uuid"],
                        "organization_id": row["organization_id"],
                        "user_id": row["user_id"],
                        "role_code": row["role_code"],
                        "status": row["effective_status"],
                        "invited_by_id": row.get("invited_by_id"),
                        "joined_at": row.get("joined_at"),
                        "permissions": row.get("permissions") or {},
                        "presence": "online" if row.get("user_is_online") else "offline",
                        "last_active_at": row.get("last_active_at"),
                        "user": (
                            {
                                "uuid": row["user_uuid"],
                                "email": row["user_email"],
                                "full_name": row.get("user_full_name"),
                                "avatar": row.get("user_avatar"),
                                "avatar_bg": None,
                            }
                            if row.get("user_uuid") and row.get("user_email")
                            else None
                        ),
                    }
                )

            return items, int(count_result.scalar_one())
        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to list organization members with user details",
                internal_details=str(e),
            ) from e
