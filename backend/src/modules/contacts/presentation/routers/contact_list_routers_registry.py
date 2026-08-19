from fastapi import APIRouter

from src.modules.contacts.presentation.routers.contact_list_routers import (
    router as contact_list_router,
)
from src.modules.contacts.presentation.routers.sheets_routers import (
    private_router as sheets_private_router,
    public_router as sheets_public_router,
)


def register_contact_list_routers(main_router: APIRouter):
    main_router.include_router(
        contact_list_router,
        prefix="/contact-lists",
        tags=["Contacts - Lists"],
    )
    main_router.include_router(
        sheets_public_router,
        prefix="/contact-lists",
        tags=["Contacts - Sheets"],
    )
    main_router.include_router(
        sheets_private_router,
        prefix="/contact-lists",
        tags=["Contacts - Sheets"],
    )
