from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.campaign.application.services import CampaignService


class CampaignContainer(containers.DeclarativeContainer):
    session = providers.Dependency(instance_of=AsyncSession)

    campaign_service = providers.Factory(
        CampaignService,
        session=session,
    )


def get_campaign_container(session: AsyncSession) -> CampaignContainer:
    container = CampaignContainer()
    container.session.override(session)
    return container
