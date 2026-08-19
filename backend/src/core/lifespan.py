from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.config.settings import config
from src.shared.infrastructure.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.shared.infrastructure.background_task_manager.deletion_cleanup import (
        deletion_cleanup_loop,
    )
    from src.modules.organization.infrastructure.background_tasks.organization_deletion_cleanup_task import (
    organization_deletion_cleanup_task,
)
    from src.shared.infrastructure.background_task_manager.task_manager import task_manager
    from src.shared.infrastructure.redis_client import close_redis
    from src.shared.mediator.discover import auto_discover_listeners
    from src.modules.email_account.infrastructure.background_tasks.email_health_cleanup import (
        health_check_loop,
        stale_reconnect_loop,
        expired_verification_cleanup_loop,
    )

    logger.info(f"Starting {config.PROJECT_NAME} in {config.ENVIRONMENT} environment")
    auto_discover_listeners()

    task_manager.add_task(deletion_cleanup_loop())
    task_manager.add_task(organization_deletion_cleanup_task())
    task_manager.add_task(health_check_loop())
    task_manager.add_task(stale_reconnect_loop())
    task_manager.add_task(expired_verification_cleanup_loop())
    
    await task_manager.start()

    yield

    await task_manager.stop()
    await close_redis()
    logger.info(f"Shutting down {config.PROJECT_NAME}")
