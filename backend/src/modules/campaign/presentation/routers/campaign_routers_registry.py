from fastapi import APIRouter

from src.modules.campaign.presentation.routers.campaign_routers import router


def register_campaign_routers(main_router: APIRouter) -> None:
    main_router.include_router(router, prefix="/campaigns", tags=["Campaigns"])
