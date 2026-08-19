from fastapi import APIRouter

from src.modules.email_account.presentation.routers.email_account_routers import (
    router as email_account_router,
)


def register_email_account_routers(router: APIRouter):
    router.include_router(
        email_account_router,
        prefix="/email-accounts",
        tags=["Email Account"],
    )