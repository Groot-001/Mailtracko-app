"""Dramatiq workers for scheduled and running Campaign delivery.

Run a worker with:
uv run dramatiq src.modules.campaign.infrastructure.background_tasks.campaign_tasks

The scheduler actor can be invoked from cron once per minute:
uv run dramatiq-gevent ...  # or call enqueue_due_campaigns.send()
"""

import asyncio
from datetime import UTC, datetime

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from sqlalchemy import or_, select, text

from src.core.config.settings import config

from src.modules.auth.infrastructure.models.user_model import (
    UserModel,
)
from src.modules.campaign.application.services import (
    CampaignService,
)
from src.modules.campaign.domain.enums import (
    ABTestStatus,
    CampaignStatus,
)
from src.modules.campaign.infrastructure.models import (
    CampaignABTestModel,
    CampaignModel,
    CampaignRecipientModel,
)
from src.modules.campaign.infrastructure.uow import (
    CampaignUOW,
)
from src.modules.contacts.infrastructure.models.contact_models import (
    ContactListModel,
    ContactModel,
)
from src.modules.email_account.infrastructure.models.email_account_model import (
    EmailAccountModel,
)
from src.modules.email_template.infrastructure.models.template_model import (
    TemplateModel,
)
from src.modules.organization.infrastructure.models.organization_model import (
    OrganizationModel,
)
from src.shared.infrastructure.db import (
    create_worker_session_factory,
)
from src.shared.infrastructure.logger import logger
from src.shared.exceptions.base_exceptions import ConflictError, InvalidError


# Register all external SQLAlchemy models referenced by Campaign foreign keys.
#
# Campaign models reference:
# - sys_auth_users
# - org_organizations
# - email_accounts
# - templates
# - contact_lists
# - contact_contacts
#
# Importing these models ensures their tables exist in the shared
# SQLAlchemy metadata when the Dramatiq worker starts.
_ = UserModel
_ = OrganizationModel
_ = EmailAccountModel
_ = TemplateModel
_ = ContactListModel
_ = ContactModel


broker = RedisBroker(
    url=config.DRAMATIQ_BROKER_URL
)
dramatiq.set_broker(broker)


def _run(coro):
    return asyncio.run(coro)


@dramatiq.actor(
    max_retries=3,
    min_backoff=5_000,
    max_backoff=60_000,
)
def process_campaign_batch(
    campaign_id: int,
) -> None:
    try:
        _run(
            _process_campaign_batch(
                campaign_id
            )
        )
    except (InvalidError, ConflictError) as exc:
        # These are expected campaign-state/validation outcomes, not worker
        # infrastructure failures.  A scheduled campaign can become invalid
        # after it was scheduled (for example if its sender account becomes
        # unavailable).  Do not let Dramatiq retry the same non-ready batch
        # several times; the scheduler will naturally evaluate the campaign
        # again later after the user fixes the underlying configuration.
        logger.warning(
            "Campaign worker skipped campaign_id=%s: %s; details=%s",
            campaign_id,
            exc.error,
            exc.errors,
        )
        return


async def _process_campaign_batch(
    campaign_id: int,
) -> None:
    session_factory = (
        create_worker_session_factory()
    )

    async with session_factory() as session:
        async with CampaignUOW(session):
            campaign = await session.get(
                CampaignModel,
                campaign_id,
            )

            if (
                not campaign
                or campaign.deleted_at is not None
            ):
                return

            if campaign.status not in {
                CampaignStatus.SCHEDULED.value,
                CampaignStatus.RUNNING.value,
            }:
                return

            actor_id = campaign.created_by_id

            if actor_id is None:
                actor_id = (
                    await session.execute(
                        text(
                            "SELECT user_id "
                            "FROM org_organization_members "
                            "WHERE organization_id = :organization_id "
                            "AND status = 'active' "
                            "AND deleted_at IS NULL "
                            "ORDER BY id "
                            "LIMIT 1"
                        ),
                        {
                            "organization_id":
                                campaign.organization_id
                        },
                    )
                ).scalar_one_or_none()

            if actor_id is None:
                logger.error(
                    "Campaign worker cannot resolve "
                    "an actor for campaign_id=%s",
                    campaign_id,
                )
                return

            service = CampaignService(
                session
            )

            result = (
                await service.process_campaign(
                    campaign=campaign,
                    actor_id=int(actor_id),
                    dry_run=False,
                    limit=campaign.batch_size,
                )
            )

            logger.info(
                "Campaign worker processed "
                "campaign_id=%s "
                "processed=%s "
                "sent=%s "
                "failed=%s "
                "completed=%s",
                campaign_id,
                result["processed"],
                result["sent"],
                result["failed"],
                result["completed"],
            )


@dramatiq.actor(
    max_retries=1
)
def enqueue_due_campaigns() -> None:
    _run(
        _enqueue_due_campaigns()
    )


@dramatiq.actor(
    max_retries=1
)
def evaluate_ab_test_winners() -> None:
    _run(
        _evaluate_ab_test_winners()
    )


async def _enqueue_due_campaigns() -> None:
    session_factory = (
        create_worker_session_factory()
    )

    async with session_factory() as session:
        now = datetime.now(UTC)

        due_scheduled = (
            await session.execute(
                select(
                    CampaignModel.id
                ).where(
                    CampaignModel.status
                    == CampaignStatus.SCHEDULED.value,
                    CampaignModel.deleted_at.is_(
                        None
                    ),
                    CampaignModel.scheduled_at.is_not(
                        None
                    ),
                    CampaignModel.scheduled_at
                    <= now,
                )
            )
        ).scalars().all()

        due_running = (
            await session.execute(
                select(
                    CampaignModel.id
                )
                .join(
                    CampaignRecipientModel,
                    CampaignRecipientModel.campaign_id
                    == CampaignModel.id,
                )
                .where(
                    CampaignModel.status
                    == CampaignStatus.RUNNING.value,
                    CampaignModel.deleted_at.is_(
                        None
                    ),
                    CampaignRecipientModel.status.in_(
                        [
                            "pending",
                            "queued",
                        ]
                    ),
                    or_(
                        CampaignRecipientModel.next_attempt_at.is_(
                            None
                        ),
                        CampaignRecipientModel.next_attempt_at
                        <= now,
                    ),
                )
                .distinct()
            )
        ).scalars().all()

        for campaign_id in (
            set(due_scheduled)
            | set(due_running)
        ):
            process_campaign_batch.send(
                int(campaign_id)
            )

        evaluate_ab_test_winners.send()


async def _evaluate_ab_test_winners() -> None:
    session_factory = (
        create_worker_session_factory()
    )

    async with session_factory() as session:
        async with CampaignUOW(session):
            campaign_ids = (
                await session.execute(
                    select(
                        CampaignABTestModel.campaign_id
                    ).where(
                        CampaignABTestModel.status
                        == ABTestStatus.RUNNING.value,
                        CampaignABTestModel.auto_select_winner.is_(
                            True
                        ),
                        CampaignABTestModel.winner_variant_id.is_(
                            None
                        ),
                    )
                )
            ).scalars().all()

            service = CampaignService(
                session
            )

            for campaign_id in campaign_ids:
                campaign = await session.get(
                    CampaignModel,
                    int(campaign_id),
                )

                if (
                    campaign
                    and campaign.deleted_at
                    is None
                ):
                    await service._maybe_select_ab_winner(
                        campaign
                    )