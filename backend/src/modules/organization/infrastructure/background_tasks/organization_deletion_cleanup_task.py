import asyncio
from datetime import UTC, datetime

from sqlalchemy import text

from src.modules.organization.domain.events.organization_domain_events import (
    OrganizationDeletedEvent,
)
from src.shared.infrastructure.db import async_session
from src.shared.infrastructure.logger import logger
from src.shared.mediator.mediator import mediator

CHECK_INTERVAL_SECONDS = 300

async def process_requested_organization_deletions():
    """
    Soft-deletes organizations whose scheduled deletion time has passed.

    This handles:
    - owner requested organization deletion
    - scheduled_deletion_at has passed
    - organization is finally soft-deleted
    - owner and members are sent to auth module through OrganizationDeletedEvent
    """
    events_to_publish: list[OrganizationDeletedEvent] = []

    try:
        async with async_session() as session:
            now = datetime.now(UTC)

            organizations_result = await session.execute(
                text(
                    "SELECT id, uuid, name, owner_id, deletion_requested_by_id "
                    "FROM org_organizations "
                    "WHERE scheduled_deletion_at IS NOT NULL "
                    "AND scheduled_deletion_at <= :now "
                    "AND deleted_at IS NULL"
                ),
                {"now": now},
            )

            organizations = organizations_result.mappings().all()

            if not organizations:
                return

            for organization in organizations:
                organization_id = organization["id"]
                organization_uuid = str(organization["uuid"])
                organization_name = organization["name"]
                owner_id = organization["owner_id"]
                deletion_requested_by_id = organization["deletion_requested_by_id"]
                actor_id = deletion_requested_by_id or owner_id

                members_result = await session.execute(
                    text(
                        "SELECT DISTINCT user_id "
                        "FROM org_organization_members "
                        "WHERE organization_id = :organization_id "
                        "AND deleted_at IS NULL"
                    ),
                    {"organization_id": organization_id},
                )

                deleted_user_ids = [
                    row["user_id"] for row in members_result.mappings().all()
                ]

                await session.execute(
                    text(
                        "UPDATE org_organizations "
                        "SET status = 'suspended', "
                        "deleted_at = :now, "
                        "updated_by_id = :actor_id, "
                        "updated_at = :now "
                        "WHERE id = :organization_id "
                        "AND deleted_at IS NULL"
                    ),
                    {
                        "now": now,
                        "actor_id": actor_id,
                        "organization_id": organization_id,
                    },
                )

                await session.execute(
                    text(
                        "UPDATE org_organization_members "
                        "SET status = 'removed', "
                        "deleted_at = :now, "
                        "updated_by_id = :actor_id, "
                        "updated_at = :now "
                        "WHERE organization_id = :organization_id "
                        "AND deleted_at IS NULL"
                    ),
                    {
                        "now": now,
                        "actor_id": actor_id,
                        "organization_id": organization_id,
                    },
                )

                await session.execute(
                    text(
                        "UPDATE org_organization_invitations "
                        "SET status = 'revoked', "
                        "revoked_at = :now, "
                        "updated_by_id = :actor_id, "
                        "updated_at = :now "
                        "WHERE organization_id = :organization_id "
                        "AND status = 'pending'"
                    ),
                    {
                        "now": now,
                        "actor_id": actor_id,
                        "organization_id": organization_id,
                    },
                )

                events_to_publish.append(
                    OrganizationDeletedEvent(
                        organization_id=organization_id,
                        organization_uuid=organization_uuid,
                        organization_name=organization_name,
                        deleted_user_ids=deleted_user_ids,
                        deleted_by_id=actor_id,
                        deleted_at=now,
                    )
                )

                logger.info(
                    "[OrganizationCleanupTask] Soft-deleted scheduled organization_id=%s",
                    organization_id,
                )

            await session.commit()

            logger.info(
                "[OrganizationCleanupTask] Processed %d scheduled organization deletion(s)",
                len(organizations),
            )

        for event in events_to_publish:
            await mediator.publish(event)

    except Exception as e:
        logger.error(
            "[OrganizationCleanupTask] Failed to process scheduled organization deletions: %s",
            str(e),
        )


async def process_deleted_user_organization_cleanup():
    """
    Cleans organization data after auth module soft-deletes users.

    If deleted user is organization owner:
    - soft delete organization
    - mark all organization members as removed
    - revoke pending invitations
    - publish OrganizationDeletedEvent so auth can delete remaining members

    If deleted user is admin/member:
    - mark only that user's membership as removed
    """
    events_to_publish: list[OrganizationDeletedEvent] = []

    try:
        async with async_session() as session:
            now = datetime.now(UTC)

            deleted_members_result = await session.execute(
                text(
                    "SELECT om.id, om.organization_id, om.user_id, om.role_code "
                    "FROM org_organization_members om "
                    "JOIN sys_auth_users u ON u.id = om.user_id "
                    "WHERE u.deleted_at IS NOT NULL "
                    "AND om.status = 'active' "
                    "AND om.deleted_at IS NULL"
                )
            )

            deleted_members = deleted_members_result.mappings().all()

            if not deleted_members:
                return

            for member in deleted_members:
                organization_id = member["organization_id"]
                user_id = member["user_id"]
                role_code = member["role_code"]

                if role_code == "owner":
                    organization_result = await session.execute(
                        text(
                            "SELECT id, uuid, name "
                            "FROM org_organizations "
                            "WHERE id = :organization_id "
                            "LIMIT 1"
                        ),
                        {"organization_id": organization_id},
                    )

                    organization = organization_result.mappings().one_or_none()

                    members_result = await session.execute(
                        text(
                            "SELECT DISTINCT user_id "
                            "FROM org_organization_members "
                            "WHERE organization_id = :organization_id "
                            "AND deleted_at IS NULL"
                        ),
                        {"organization_id": organization_id},
                    )

                    deleted_user_ids = [
                        row["user_id"] for row in members_result.mappings().all()
                    ]

                    await session.execute(
                        text(
                            "UPDATE org_organizations "
                            "SET status = 'suspended', "
                            "deleted_at = :now, "
                            "updated_by_id = :user_id, "
                            "updated_at = :now "
                            "WHERE id = :organization_id "
                            "AND deleted_at IS NULL"
                        ),
                        {
                            "now": now,
                            "user_id": user_id,
                            "organization_id": organization_id,
                        },
                    )

                    await session.execute(
                        text(
                            "UPDATE org_organization_members "
                            "SET status = 'removed', "
                            "deleted_at = :now, "
                            "updated_by_id = :user_id, "
                            "updated_at = :now "
                            "WHERE organization_id = :organization_id "
                            "AND deleted_at IS NULL"
                        ),
                        {
                            "now": now,
                            "user_id": user_id,
                            "organization_id": organization_id,
                        },
                    )

                    await session.execute(
                        text(
                            "UPDATE org_organization_invitations "
                            "SET status = 'revoked', "
                            "revoked_at = :now, "
                            "updated_by_id = :user_id, "
                            "updated_at = :now "
                            "WHERE organization_id = :organization_id "
                            "AND status = 'pending'"
                        ),
                        {
                            "now": now,
                            "user_id": user_id,
                            "organization_id": organization_id,
                        },
                    )

                    if organization:
                        events_to_publish.append(
                            OrganizationDeletedEvent(
                                organization_id=organization_id,
                                organization_uuid=str(organization["uuid"]),
                                organization_name=organization["name"],
                                deleted_user_ids=deleted_user_ids,
                                deleted_by_id=user_id,
                                deleted_at=now,
                            )
                        )

                    logger.info(
                        "[OrganizationCleanupTask] Soft-deleted organization_id=%s because owner user_id=%s was deleted",
                        organization_id,
                        user_id,
                    )

                else:
                    await session.execute(
                        text(
                            "UPDATE org_organization_members "
                            "SET status = 'removed', "
                            "deleted_at = :now, "
                            "updated_by_id = :user_id, "
                            "updated_at = :now "
                            "WHERE user_id = :user_id "
                            "AND deleted_at IS NULL"
                        ),
                        {
                            "now": now,
                            "user_id": user_id,
                        },
                    )

                    logger.info(
                        "[OrganizationCleanupTask] Removed organization membership for deleted user_id=%s",
                        user_id,
                    )

            await session.commit()

            logger.info(
                "[OrganizationCleanupTask] Processed %d deleted organization member(s)",
                len(deleted_members),
            )

        for event in events_to_publish:
            await mediator.publish(event)

    except Exception as e:
        logger.error(
            "[OrganizationCleanupTask] Failed to process organization cleanup: %s",
            str(e),
        )


async def process_organization_cleanup():
    """
    Runs all organization cleanup jobs.
    """
    await process_requested_organization_deletions()
    await process_deleted_user_organization_cleanup()


async def organization_deletion_cleanup_task():
    """
    Run organization cleanup loop every CHECK_INTERVAL_SECONDS.
    """
    while True:
        await process_organization_cleanup()
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)