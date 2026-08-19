from fastapi import APIRouter

from src.modules.platform.presentation.admin_routers import router as admin_router
from src.modules.platform.presentation.billing_routers import router as billing_router
from src.modules.platform.presentation.support_routers import router as support_router
from src.modules.platform.presentation.workspace_routers import (
    router as workspace_router,
)


def register_platform_routers(main_router: APIRouter) -> None:
    main_router.include_router(workspace_router, tags=["Platform"])
    main_router.include_router(billing_router, tags=["Billing"])
    main_router.include_router(support_router, tags=["Support"])
    main_router.include_router(admin_router, tags=["Platform Admin"])
