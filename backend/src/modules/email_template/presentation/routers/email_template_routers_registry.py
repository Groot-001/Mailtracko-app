from fastapi import APIRouter

from src.modules.email_template.presentation.routers.email_template_routers import (
    router as email_template_router,
)


def register_email_template_routers(
    router: APIRouter,
):
    """
    Registers email template routers.
    """
    router.include_router(
        email_template_router,
        tags=["Email Template - Core"],
    )