from fastapi import APIRouter

from src.modules.organization.presentation.routers.organization_routers import (
    router as organization_router,
)


def register_organization_routers(router: APIRouter):
    """
    Registers organization routers.
    """
    router.include_router(
        organization_router,
        prefix="/organizations",
        tags=["Organization - Core"],
    )