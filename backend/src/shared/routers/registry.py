from fastapi import APIRouter

from src.modules.auth.presentation.routers.auth_routers_registry import (
    register_auth_routers,
)
from src.modules.email_template.presentation.routers.email_template_routers_registry import (
    register_email_template_routers,
)
from src.modules.organization.presentation.routers.organization_routers_registry import (
    register_organization_routers,
)
from src.modules.email_account.presentation.routers.email_account_routers_registry import (
    register_email_account_routers,
)
from src.modules.contacts.presentation.routers.contact_list_routers_registry import (
    register_contact_list_routers,
)
from src.modules.campaign.presentation.routers.campaign_routers_registry import (
    register_campaign_routers,
)
from src.modules.platform.presentation.routers_registry import register_platform_routers


main_router = APIRouter(prefix="/api/v1")


def register_routers(app):
    register_auth_routers(main_router)
    register_organization_routers(main_router)
    register_email_account_routers(main_router)
    register_email_template_routers(main_router)
    register_contact_list_routers(main_router)
    register_campaign_routers(main_router)
    register_platform_routers(main_router)

    app.include_router(main_router)
