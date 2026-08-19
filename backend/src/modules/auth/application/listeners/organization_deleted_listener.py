from sqlalchemy import bindparam, text

from src.modules.organization.domain.events.organization_domain_events import (
    OrganizationDeletedEvent,
)
from src.shared.infrastructure.db import async_session
from src.shared.infrastructure.logger import logger
from src.shared.mediator.listener import listener


@listener(OrganizationDeletedEvent)
async def on_organization_deleted_soft_delete_users(
    event: OrganizationDeletedEvent,
):
    """
    Soft-deletes owner and members after their organization is finally deleted.
    """
    if not event.deleted_user_ids:
        return

    try:
        async with async_session() as session:
            statement = text(
                "UPDATE sys_auth_users "
                "SET deleted_at = :deleted_at, "
                "updated_at = :deleted_at "
                "WHERE id IN :user_ids "
                "AND deleted_at IS NULL"
            ).bindparams(
                bindparam("user_ids", expanding=True),
            )

            result = await session.execute(
                statement,
                {
                    "deleted_at": event.deleted_at,
                    "user_ids": event.deleted_user_ids,
                },
            )

            updated_count = getattr(result, "rowcount", 0) or 0

            await session.commit()

            logger.info(
                "[AuthOrganizationListener] Soft-deleted %d user(s) after organization_id=%s deletion",
                updated_count,
                event.organization_id,
            )

    except Exception as e:
        logger.error(
            "[AuthOrganizationListener] Failed to soft-delete users after organization deletion: %s",
            str(e),
        )