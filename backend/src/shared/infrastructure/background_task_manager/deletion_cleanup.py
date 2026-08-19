import asyncio
from datetime import UTC, datetime

from src.shared.infrastructure.db import async_session
from src.shared.infrastructure.logger import logger

CHECK_INTERVAL_SECONDS = 300


async def process_expired_deletions():
    """Soft-delete users whose scheduled deletion time has passed."""
    try:
        async with async_session() as session:
            from sqlalchemy import text

            now = datetime.now(UTC)
            result = await session.execute(
                text(
                    "UPDATE sys_auth_users "
                    "SET deleted_at = :now, updated_at = :now "
                    "WHERE scheduled_deletion_at IS NOT NULL "
                    "AND scheduled_deletion_at <= :now "
                    "AND deleted_at IS NULL"
                ),
                {"now": now},
            )
            count = result.rowcount
            if count:
                logger.info("[DeletionCleanup] Soft-deleted %d expired account(s)", count)
            await session.commit()
    except Exception as e:
        logger.error("[DeletionCleanup] Failed to process expired deletions: %s", str(e))


async def deletion_cleanup_loop():
    """Run the cleanup loop every CHECK_INTERVAL_SECONDS."""
    while True:
        await process_expired_deletions()
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
