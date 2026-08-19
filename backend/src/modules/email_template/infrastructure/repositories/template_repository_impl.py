from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, text as stmt
import json

from src.modules.campaign.domain.enums import CampaignStatus
from src.modules.campaign.infrastructure.models import (
    CampaignABVariantModel,
    CampaignModel,
    CampaignSequenceStepModel,
)
from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.modules.email_template.domain.repositories.template_repository import (
    ITemplateRepository,
)
from src.modules.email_template.infrastructure.models.template_model import (
    TemplateModel,
)
from src.shared.exceptions.base_exceptions import ServerError
from src.shared.infrastructure.repository.base_repository import (
    BaseRepository,
)


class TemplateRepositoryImpl(
    BaseRepository[TemplateEntity],
    ITemplateRepository,
):
    """
    SQLAlchemy implementation of the template repository.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.table_name = TemplateModel.__tablename__
        super().__init__(
            session,
            self.table_name,
        )

    def to_row(
        self,
        entity: TemplateEntity,
    ) -> dict:
        """
        Converts a TemplateEntity to a database row.
        """
        return {
            "id": entity.id,
            "uuid": entity.uuid,
            "organization_id": entity.organization_id,
            "category_id": entity.category_id,
            "source_template_id": entity.source_template_id,
            "name": entity.name,
            "description": entity.description,
            "subject": entity.subject,
            "preheader": entity.preheader,
            "body_html": entity.body_html,
            "from_name": entity.from_name,
            "from_email": entity.from_email,
            "tags": json.dumps(entity.tags or []),
            "template_type": entity.template_type,
            "status": entity.status,
            "is_active": entity.is_active,
            "is_default": entity.is_default,
            "smart_personalization_enabled": (
                entity.smart_personalization_enabled
            ),
            "published_at": entity.published_at,
            "archived_at": entity.archived_at,
            "created_by_id": entity.created_by_id,
            "updated_by_id": entity.updated_by_id,
            "deleted_at": entity.deleted_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def to_entity(
        self,
        row: dict,
    ) -> TemplateEntity:
        tags = row.get("tags") or []
        if isinstance(tags, str):
             tags = json.loads(tags)
        """
        Converts a database row to TemplateEntity.
        """
        return TemplateEntity(
            id=row["id"],
            uuid=row["uuid"],
            organization_id=row.get("organization_id"),
            category_id=row.get("category_id"),
            source_template_id=row.get("source_template_id"),
            name=row["name"],
            description=row.get("description"),
            subject=row["subject"],
            preheader=row.get("preheader"),
            body_html=row["body_html"],
            from_name=row.get("from_name"),
            from_email=row.get("from_email"),
            tags=tags,
            template_type=row["template_type"],
            status=row["status"],
            is_active=row["is_active"],
            is_default=bool(
                row.get("is_default", False)
            ),
            smart_personalization_enabled=bool(
                row.get(
                    "smart_personalization_enabled",
                    False,
                )
            ),
            published_at=row.get("published_at"),
            archived_at=row.get("archived_at"),
            created_by_id=row.get("created_by_id"),
            updated_by_id=row.get("updated_by_id"),
            deleted_at=row.get("deleted_at"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_custom_by_uuid(
        self,
        *,
        template_uuid: str,
        organization_id: int,
    ) -> TemplateEntity | None:
        """
        Retrieves a custom template by UUID and organization ID.
        """
        sql = stmt(
            f"SELECT * FROM {self.table_name} "
            "WHERE uuid = :template_uuid "
            "AND organization_id = :organization_id "
            "AND template_type = 'custom' "
            "AND is_active = true "
            "AND deleted_at IS NULL "
            "LIMIT 1"
        )

        params = {
            "template_uuid": template_uuid,
            "organization_id": organization_id,
        }

        try:
            result = await self.session.execute(
                sql,
                params,
            )
            row = result.mappings().one_or_none()

            return (
                self.to_entity(dict(row))
                if row
                else None
            )

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to fetch custom template",
                internal_details=str(e),
            ) from e

    async def get_system_by_uuid(
        self,
        template_uuid: str,
    ) -> TemplateEntity | None:
        """
        Retrieves an active published system template by UUID.
        """
        sql = stmt(
            f"SELECT * FROM {self.table_name} "
            "WHERE uuid = :template_uuid "
            "AND organization_id IS NULL "
            "AND template_type = 'system' "
            "AND status = 'published' "
            "AND is_active = true "
            "AND deleted_at IS NULL "
            "LIMIT 1"
        )

        try:
            result = await self.session.execute(
                sql,
                {
                    "template_uuid": template_uuid,
                },
            )
            row = result.mappings().one_or_none()

            return (
                self.to_entity(dict(row))
                if row
                else None
            )

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to fetch system template",
                internal_details=str(e),
            ) from e

    async def list_custom_paginated(
        self,
        *,
        organization_id: int,
        status: str | None = None,
        include_archived: bool = False,
        category_id: int | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TemplateEntity], int]:
        """
        Lists organization-owned custom templates with pagination.
        """
        where_clauses = [
            "organization_id = :organization_id",
            "template_type = 'custom'",
            "is_active = true",
            "deleted_at IS NULL",
        ]

        params: dict[str, int | str] = {
            "organization_id": organization_id,
            "limit": limit,
            "offset": offset,
        }

        if status:
            where_clauses.append(
                "status = :status"
            )
            params["status"] = status
        elif not include_archived:
            where_clauses.append("status != 'archived'")

        if category_id is not None:
            where_clauses.append(
                "category_id = :category_id"
            )
            params["category_id"] = category_id

        if search:
            where_clauses.append(
                "("
                "name ILIKE :search "
                "OR subject ILIKE :search "
                "OR COALESCE(description, '') ILIKE :search "
                "OR COALESCE(preheader, '') ILIKE :search "
                "OR COALESCE(tags::text, '') ILIKE :search"
                ")"
            )
            params["search"] = (
                f"%{search.strip()}%"
            )

        where_sql = " AND ".join(
            where_clauses
        )

        list_sql = stmt(
            f"SELECT * FROM {self.table_name} "
            f"WHERE {where_sql} "
            "ORDER BY updated_at DESC, id DESC "
            "LIMIT :limit OFFSET :offset"
        )

        count_sql = stmt(
            f"SELECT COUNT(*) "
            f"FROM {self.table_name} "
            f"WHERE {where_sql}"
        )

        try:
            list_result = await self.session.execute(
                list_sql,
                params,
            )
            rows = list_result.mappings().all()

            count_params = {
                key: value
                for key, value in params.items()
                if key not in {
                    "limit",
                    "offset",
                }
            }

            count_result = await self.session.execute(
                count_sql,
                count_params,
            )

            total = int(
                count_result.scalar_one()
            )

            templates = [
                self.to_entity(dict(row))
                for row in rows
            ]

            return templates, total

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to list custom templates",
                internal_details=str(e),
            ) from e

    async def list_system_paginated(
        self,
        *,
        category_id: int | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TemplateEntity], int]:
        """
        Lists active published system templates with pagination.
        """
        where_clauses = [
            "organization_id IS NULL",
            "template_type = 'system'",
            "status = 'published'",
            "is_active = true",
            "deleted_at IS NULL",
        ]

        params: dict[str, int | str] = {
            "limit": limit,
            "offset": offset,
        }

        if category_id is not None:
            where_clauses.append(
                "category_id = :category_id"
            )
            params["category_id"] = category_id

        if search:
            where_clauses.append(
                "("
                "name ILIKE :search "
                "OR subject ILIKE :search "
                "OR COALESCE(description, '') ILIKE :search "
                "OR COALESCE(preheader, '') ILIKE :search "
                "OR COALESCE(tags::text, '') ILIKE :search"
                ")"
            )
            params["search"] = (
                f"%{search.strip()}%"
            )

        where_sql = " AND ".join(
            where_clauses
        )

        list_sql = stmt(
            f"SELECT * FROM {self.table_name} "
            f"WHERE {where_sql} "
            "ORDER BY updated_at DESC, id DESC "
            "LIMIT :limit OFFSET :offset"
        )

        count_sql = stmt(
            f"SELECT COUNT(*) "
            f"FROM {self.table_name} "
            f"WHERE {where_sql}"
        )

        try:
            list_result = await self.session.execute(
                list_sql,
                params,
            )
            rows = list_result.mappings().all()

            count_params = {
                key: value
                for key, value in params.items()
                if key not in {
                    "limit",
                    "offset",
                }
            }

            count_result = await self.session.execute(
                count_sql,
                count_params,
            )

            total = int(
                count_result.scalar_one()
            )

            templates = [
                self.to_entity(dict(row))
                for row in rows
            ]

            return templates, total

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to list system templates",
                internal_details=str(e),
            ) from e

    async def unset_default_for_organization(
        self,
        *,
        organization_id: int,
        updated_by_id: int,
        exclude_template_id: int | None = None,
    ) -> None:
        """
        Removes the default flag from other custom templates.
        """
        where_clauses = [
            "organization_id = :organization_id",
            "template_type = 'custom'",
            "is_default = true",
            "deleted_at IS NULL",
        ]

        params: dict[str, int] = {
            "organization_id": organization_id,
            "updated_by_id": updated_by_id,
        }

        if exclude_template_id is not None:
            where_clauses.append(
                "id != :exclude_template_id"
            )
            params["exclude_template_id"] = (
                exclude_template_id
            )

        where_sql = " AND ".join(
            where_clauses
        )

        sql = stmt(
            f"UPDATE {self.table_name} "
            "SET is_default = false, "
            "updated_by_id = :updated_by_id, "
            "updated_at = NOW() "
            f"WHERE {where_sql}"
        )

        try:
            await self.session.execute(
                sql,
                params,
            )

        except SQLAlchemyError as e:
            raise ServerError(
                error=(
                    "Failed to update default template"
                ),
                internal_details=str(e),
            ) from e

    async def get_dashboard_counts(
        self,
        *,
        organization_id: int,
    ) -> dict[str, int]:
        """
        Returns template counts for the organization dashboard.
        """
        sql = stmt(
            f"SELECT "
            "COUNT(*) AS total_templates, "
            "COUNT(*) FILTER "
            "(WHERE status = 'draft') "
            "AS draft_templates, "
            "COUNT(*) FILTER "
            "(WHERE status = 'published') "
            "AS published_templates, "
            "COUNT(*) FILTER "
            "(WHERE status = 'archived') "
            "AS archived_templates "
            f"FROM {self.table_name} "
            "WHERE organization_id = :organization_id "
            "AND template_type = 'custom' "
            "AND is_active = true "
            "AND deleted_at IS NULL"
        )

        try:
            result = await self.session.execute(
                sql,
                {
                    "organization_id": organization_id,
                },
            )
            row = result.mappings().one()

            return {
                "total_templates": int(
                    row["total_templates"]
                ),
                "draft_templates": int(
                    row["draft_templates"]
                ),
                "published_templates": int(
                    row["published_templates"]
                ),
                "archived_templates": int(
                    row["archived_templates"]
                ),
            }

        except SQLAlchemyError as e:
            raise ServerError(
                error=(
                    "Failed to retrieve template dashboard counts"
                ),
                internal_details=str(e),
            ) from e

    async def count_campaign_usages(
        self,
        *,
        template_id: int,
        organization_id: int,
    ) -> int:
        """
        Counts campaign references to a template across regular, sequence,
        and A/B variant configurations.
        """
        direct_campaign_count = (
            select(func.count())
            .select_from(CampaignModel)
            .where(
                CampaignModel.organization_id == organization_id,
                CampaignModel.deleted_at.is_(None),
                CampaignModel.status.not_in({
                    CampaignStatus.COMPLETED.value,
                    CampaignStatus.CANCELLED.value,
                    CampaignStatus.FAILED.value,
                    CampaignStatus.ARCHIVED.value,
                }),
                CampaignModel.template_id == template_id,
            )
            .scalar_subquery()
        )

        sequence_step_count = (
            select(func.count())
            .select_from(CampaignSequenceStepModel)
            .join(
                CampaignModel,
                CampaignModel.id == CampaignSequenceStepModel.campaign_id,
            )
            .where(
                CampaignModel.organization_id == organization_id,
                CampaignModel.deleted_at.is_(None),
                CampaignModel.status.not_in({
                    CampaignStatus.COMPLETED.value,
                    CampaignStatus.CANCELLED.value,
                    CampaignStatus.FAILED.value,
                    CampaignStatus.ARCHIVED.value,
                }),
                CampaignSequenceStepModel.template_id == template_id,
            )
            .scalar_subquery()
        )

        ab_variant_count = (
            select(func.count())
            .select_from(CampaignABVariantModel)
            .join(
                CampaignModel,
                CampaignModel.id == CampaignABVariantModel.campaign_id,
            )
            .where(
                CampaignModel.organization_id == organization_id,
                CampaignModel.deleted_at.is_(None),
                CampaignModel.status.not_in({
                    CampaignStatus.COMPLETED.value,
                    CampaignStatus.CANCELLED.value,
                    CampaignStatus.FAILED.value,
                    CampaignStatus.ARCHIVED.value,
                }),
                CampaignABVariantModel.template_id == template_id,
            )
            .scalar_subquery()
        )

        statement = select(
            (direct_campaign_count + sequence_step_count + ab_variant_count).label(
                "total_usage"
            )
        )

        try:
            result = await self.session.execute(
                statement
            )
            total = result.scalar_one()
            return int(total or 0)

        except SQLAlchemyError as e:
            raise ServerError(
                error="Failed to check template campaign usage",
                internal_details=str(e),
            ) from e