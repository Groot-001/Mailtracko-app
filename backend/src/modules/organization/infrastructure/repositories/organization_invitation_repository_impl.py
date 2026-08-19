from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from src.modules.organization.domain.entities.organization_invitation_entity import (
    OrganizationInvitationEntity,
)
from src.modules.organization.domain.repositories.organization_invitation_repository import (
    IOrganizationInvitationRepository,
)
from src.modules.organization.infrastructure.models.organization_invitation_model import (
    OrganizationInvitationModel,
)
from src.shared.exceptions.base_exceptions import ServerError
from src.shared.infrastructure.repository.base_repository import BaseRepository


class OrganizationInvitationRepositoryImpl(
    BaseRepository[OrganizationInvitationEntity],
    IOrganizationInvitationRepository,
):
    """
    SQLAlchemy implementation of the organization invitation repository.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.table_name = OrganizationInvitationModel.__tablename__
        super().__init__(session, self.table_name)

    def to_row(self, entity: OrganizationInvitationEntity) -> dict:
        """
        Convert an OrganizationInvitationEntity to a database row.
        """
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "organization_id": entity.organization_id,
            "email": entity.email,
            "role_code": entity.role_code,
            "token_hash": entity.token_hash,
            "status": entity.status,
            "invited_by_id": entity.invited_by_id,
            "expires_at": entity.expires_at,
            "accepted_at": entity.accepted_at,
            "declined_at": entity.declined_at,
            "revoked_at": entity.revoked_at,
            "created_by_id": entity.created_by_id,
            "updated_by_id": entity.updated_by_id,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(self, row: dict) -> OrganizationInvitationEntity:
        """
        Convert a database row to OrganizationInvitationEntity.
        """
        return OrganizationInvitationEntity(
            id=row["id"],
            uuid=row["uuid"],
            organization_id=row["organization_id"],
            email=row["email"],
            role_code=row["role_code"],
            token_hash=row["token_hash"],
            status=row["status"],
            invited_by_id=row["invited_by_id"],
            expires_at=row["expires_at"],
            accepted_at=row.get("accepted_at"),
            declined_at=row.get("declined_at"),
            revoked_at=row.get("revoked_at"),
            created_by_id=row.get("created_by_id"),
            updated_by_id=row.get("updated_by_id"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_by_token_hash(
        self,
        token_hash: str,
    ) -> OrganizationInvitationEntity | None:
        """
        Retrieves invitation by token hash.
        """
        sql = text(
            f"SELECT * FROM {self.table_name} "
            "WHERE token_hash = :token_hash "
            "LIMIT 1"
        )

        try:
            result = await self.session.execute(sql, {"token_hash": token_hash})
            row = result.mappings().one_or_none()
            return self.to_entity(dict(row)) if row else None

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to fetch organization invitation by token hash",
                internal_details=str(e),
            ) from e

    async def get_pending_by_email(
        self,
        *,
        organization_id: int,
        email: str,
    ) -> OrganizationInvitationEntity | None:
        """
        Retrieves pending invitation by organization ID and email.
        """
        sql = text(
            f"SELECT * FROM {self.table_name} "
            "WHERE organization_id = :organization_id "
            "AND LOWER(email) = LOWER(:email) "
            "AND status = 'pending' "
            "LIMIT 1"
        )

        params = {
            "organization_id": organization_id,
            "email": email,
        }

        try:
            result = await self.session.execute(sql, params)
            row = result.mappings().one_or_none()
            return self.to_entity(dict(row)) if row else None

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to fetch pending organization invitation",
                internal_details=str(e),
            ) from e

    async def get_pending_by_email_global(
        self,
        email: str,
    ) -> list[OrganizationInvitationEntity]:
        """
        Retrieves all pending invitations by email across all organizations.
        """
        sql = text(
            f"SELECT * FROM {self.table_name} "
            "WHERE LOWER(email) = LOWER(:email) "
            "AND status = 'pending'"
        )

        try:
            result = await self.session.execute(sql, {"email": email})
            rows = result.mappings().all()
            return [self.to_entity(dict(row)) for row in rows]
        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to fetch pending invitations by email",
                internal_details=str(e),
            ) from e

    async def list_paginated(
        self,
        *,
        organization_id: int,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[OrganizationInvitationEntity], int]:
        """
        Lists organization invitations with pagination.
        """
        where_clauses = ["organization_id = :organization_id"]

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
                error="Failed to list organization invitations",
                internal_details=str(e),
            ) from e