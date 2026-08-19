from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.campaign.domain.enums import CampaignStatus
from src.modules.campaign.infrastructure.models import (
    CampaignABTestModel,
    CampaignABVariantModel,
    CampaignMessageEventModel,
    CampaignMessageModel,
    CampaignModel,
    CampaignRecipientModel,
    CampaignSequenceModel,
    CampaignSequenceStepModel,
    CampaignStateHistoryModel,
    CampaignSuppressionModel,
)


class CampaignRepositoryImpl:
    """Persistence gateway for Campaign-owned tables only."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_campaign(self, campaign: CampaignModel) -> CampaignModel:
        self.session.add(campaign)
        await self.session.flush()
        await self.session.refresh(campaign)
        return campaign

    async def get_campaign(
        self,
        campaign_uuid: str,
        organization_id: int,
        *,
        include_archived: bool = False,
    ) -> CampaignModel | None:
        stmt = select(CampaignModel).where(
            CampaignModel.uuid == campaign_uuid,
            CampaignModel.organization_id == organization_id,
        )
        if not include_archived:
            stmt = stmt.where(CampaignModel.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_campaigns(
        self,
        organization_id: int,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
        status: str | None = None,
        campaign_type: str | None = None,
        email_account_id: int | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        include_archived: bool = False,
    ) -> tuple[list[CampaignModel], int]:
        conditions = [CampaignModel.organization_id == organization_id]
        if not include_archived:
            conditions.append(CampaignModel.deleted_at.is_(None))
        if search:
            conditions.append(CampaignModel.name.ilike(f"%{search.strip()}%"))
        if status:
            conditions.append(CampaignModel.status == status)
        else:
            conditions.append(CampaignModel.status != CampaignStatus.ARCHIVED.value)
        if campaign_type:
            conditions.append(CampaignModel.campaign_type == campaign_type)
        if email_account_id is not None:
            conditions.append(CampaignModel.email_account_id == email_account_id)
        if created_from is not None:
            conditions.append(CampaignModel.created_at >= created_from)
        if created_to is not None:
            conditions.append(CampaignModel.created_at <= created_to)

        count_stmt = select(func.count(CampaignModel.id)).where(*conditions)
        total = int((await self.session.execute(count_stmt)).scalar() or 0)
        stmt = (
            select(CampaignModel)
            .where(*conditions)
            .order_by(
                CampaignModel.updated_at.desc().nullslast(),
                CampaignModel.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total

    async def dashboard_summary(self, organization_id: int) -> dict[str, int]:
        stmt = (
            select(CampaignModel.status, func.count(CampaignModel.id))
            .where(
                CampaignModel.organization_id == organization_id,
                CampaignModel.deleted_at.is_(None),
            )
            .group_by(CampaignModel.status)
        )
        rows = (await self.session.execute(stmt)).all()
        counts = {status: int(count) for status, count in rows}
        active = sum(counts.get(value, 0) for value in ("launching", "running"))
        return {
            "total_campaigns": sum(counts.values()),
            "active": active,
            "scheduled": counts.get("scheduled", 0),
            "paused": counts.get("paused", 0),
            "drafts": counts.get("draft", 0) + counts.get("ready", 0),
            "completed": counts.get("completed", 0),
            "failed": counts.get("failed", 0),
        }

    async def add_state_history(
        self,
        *,
        campaign: CampaignModel,
        from_status: str,
        to_status: str,
        actor_id: int | None,
        reason: str | None,
        transitioned_at: datetime,
    ) -> CampaignStateHistoryModel:
        history = CampaignStateHistoryModel(
            organization_id=campaign.organization_id,
            campaign_id=campaign.id,
            actor_id=actor_id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            transitioned_at=transitioned_at,
        )
        self.session.add(history)
        await self.session.flush()
        return history

    async def delete_recipients(self, campaign_id: int) -> None:
        await self.session.execute(
            delete(CampaignRecipientModel).where(
                CampaignRecipientModel.campaign_id == campaign_id
            )
        )
        await self.session.flush()

    async def add_recipients(
        self, recipients: list[CampaignRecipientModel]
    ) -> list[CampaignRecipientModel]:
        self.session.add_all(recipients)
        await self.session.flush()
        return recipients

    async def list_recipients(
        self,
        campaign_id: int,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
    ) -> tuple[list[CampaignRecipientModel], int]:
        conditions = [CampaignRecipientModel.campaign_id == campaign_id]
        if status:
            conditions.append(CampaignRecipientModel.status == status)
        total = int(
            (
                await self.session.execute(
                    select(func.count(CampaignRecipientModel.id)).where(*conditions)
                )
            ).scalar()
            or 0
        )
        rows = (
            await self.session.execute(
                select(CampaignRecipientModel)
                .where(*conditions)
                .order_by(CampaignRecipientModel.id)
                .limit(limit)
                .offset(offset)
            )
        ).scalars().all()
        return list(rows), total

    async def get_recipient(
        self, recipient_uuid: str, campaign_id: int
    ) -> CampaignRecipientModel | None:
        result = await self.session.execute(
            select(CampaignRecipientModel).where(
                CampaignRecipientModel.uuid == recipient_uuid,
                CampaignRecipientModel.campaign_id == campaign_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_due_recipients(
        self,
        campaign_id: int,
        *,
        limit: int,
    ) -> list[CampaignRecipientModel]:
        now = datetime.now(UTC)
        stmt = (
            select(CampaignRecipientModel)
            .where(
                CampaignRecipientModel.campaign_id == campaign_id,
                CampaignRecipientModel.status.in_(["pending", "queued"]),
                or_(
                    CampaignRecipientModel.next_attempt_at.is_(None),
                    CampaignRecipientModel.next_attempt_at <= now,
                ),
            )
            .order_by(CampaignRecipientModel.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def defer_due_recipients(
        self, campaign_id: int, *, next_attempt_at: datetime
    ) -> int:
        result = await self.session.execute(
            update(CampaignRecipientModel)
            .where(
                CampaignRecipientModel.campaign_id == campaign_id,
                CampaignRecipientModel.status.in_(["pending", "queued"]),
                or_(
                    CampaignRecipientModel.next_attempt_at.is_(None),
                    CampaignRecipientModel.next_attempt_at <= datetime.now(UTC),
                ),
            )
            .values(next_attempt_at=next_attempt_at, updated_at=datetime.now(UTC))
        )
        return int(result.rowcount or 0)

    async def get_sequence(
        self, campaign_id: int
    ) -> tuple[CampaignSequenceModel | None, list[CampaignSequenceStepModel]]:
        sequence = (
            await self.session.execute(
                select(CampaignSequenceModel).where(
                    CampaignSequenceModel.campaign_id == campaign_id
                )
            )
        ).scalar_one_or_none()
        if not sequence:
            return None, []
        steps = (
            await self.session.execute(
                select(CampaignSequenceStepModel)
                .where(
                    CampaignSequenceStepModel.sequence_id == sequence.id,
                    CampaignSequenceStepModel.is_enabled.is_(True),
                )
                .order_by(CampaignSequenceStepModel.step_order)
            )
        ).scalars().all()
        return sequence, list(steps)

    async def replace_sequence(
        self,
        *,
        campaign_id: int,
        organization_id: int,
        stop_on_reply: bool,
        stop_on_unsubscribe: bool,
        stop_on_click: bool,
        stop_on_meeting: bool,
        custom_stop_events: list[str],
        steps: list[dict[str, Any]],
    ) -> tuple[CampaignSequenceModel, list[CampaignSequenceStepModel]]:
        current, _ = await self.get_sequence(campaign_id)
        if current:
            await self.session.execute(
                delete(CampaignSequenceStepModel).where(
                    CampaignSequenceStepModel.sequence_id == current.id
                )
            )
            current.stop_on_reply = stop_on_reply
            current.stop_on_unsubscribe = stop_on_unsubscribe
            current.stop_on_click = stop_on_click
            current.stop_on_meeting = stop_on_meeting
            current.custom_stop_events = custom_stop_events
            current.total_steps = len(steps)
            current.status = "not_started"
            current.updated_at = datetime.now(UTC)
            sequence = current
        else:
            sequence = CampaignSequenceModel(
                campaign_id=campaign_id,
                organization_id=organization_id,
                stop_on_reply=stop_on_reply,
                stop_on_unsubscribe=stop_on_unsubscribe,
                stop_on_click=stop_on_click,
                stop_on_meeting=stop_on_meeting,
                custom_stop_events=custom_stop_events,
                total_steps=len(steps),
            )
            self.session.add(sequence)
            await self.session.flush()

        models = [
            CampaignSequenceStepModel(
                organization_id=organization_id,
                campaign_id=campaign_id,
                sequence_id=sequence.id,
                **step,
            )
            for step in steps
        ]
        self.session.add_all(models)
        await self.session.flush()
        return sequence, models

    async def get_ab_test(
        self, campaign_id: int
    ) -> tuple[CampaignABTestModel | None, list[CampaignABVariantModel]]:
        ab_test = (
            await self.session.execute(
                select(CampaignABTestModel).where(
                    CampaignABTestModel.campaign_id == campaign_id
                )
            )
        ).scalar_one_or_none()
        if not ab_test:
            return None, []
        variants = (
            await self.session.execute(
                select(CampaignABVariantModel)
                .where(CampaignABVariantModel.ab_test_id == ab_test.id)
                .order_by(CampaignABVariantModel.variant_type)
            )
        ).scalars().all()
        return ab_test, list(variants)

    async def replace_ab_test(
        self,
        *,
        campaign_id: int,
        organization_id: int,
        test_percentage: int,
        winner_metric: str,
        auto_select_winner: bool,
        minimum_sample_size: int,
        test_duration_hours: int | None,
        variants: list[dict[str, Any]],
    ) -> tuple[CampaignABTestModel, list[CampaignABVariantModel]]:
        current, _ = await self.get_ab_test(campaign_id)
        if current:
            await self.session.execute(
                delete(CampaignABVariantModel).where(
                    CampaignABVariantModel.ab_test_id == current.id
                )
            )
            current.test_percentage = test_percentage
            current.winner_metric = winner_metric
            current.auto_select_winner = auto_select_winner
            current.minimum_sample_size = minimum_sample_size
            current.test_duration_hours = test_duration_hours
            current.status = "draft"
            current.winner_variant_id = None
            current.started_at = None
            current.winner_selected_at = None
            current.updated_at = datetime.now(UTC)
            ab_test = current
        else:
            ab_test = CampaignABTestModel(
                campaign_id=campaign_id,
                organization_id=organization_id,
                test_percentage=test_percentage,
                winner_metric=winner_metric,
                auto_select_winner=auto_select_winner,
                minimum_sample_size=minimum_sample_size,
                test_duration_hours=test_duration_hours,
            )
            self.session.add(ab_test)
            await self.session.flush()

        models = [
            CampaignABVariantModel(
                organization_id=organization_id,
                campaign_id=campaign_id,
                ab_test_id=ab_test.id,
                **variant,
            )
            for variant in variants
        ]
        self.session.add_all(models)
        await self.session.flush()
        return ab_test, models

    async def assign_pending_recipients_to_variant(
        self, campaign_id: int, variant_id: int
    ) -> int:
        now = datetime.now(UTC)
        result = await self.session.execute(
            update(CampaignRecipientModel)
            .where(
                CampaignRecipientModel.campaign_id == campaign_id,
                CampaignRecipientModel.status.in_(["pending", "queued", "holdout"]),
            )
            .values(
                ab_variant_id=variant_id,
                ab_test_sampled=False,
                status="pending",
                next_attempt_at=now,
                updated_at=now,
            )
        )
        return int(result.rowcount or 0)

    async def ab_audience_counts(self, campaign_id: int) -> dict[str, int]:
        rows = (
            await self.session.execute(
                select(
                    CampaignRecipientModel.ab_test_sampled,
                    CampaignRecipientModel.status,
                    func.count(CampaignRecipientModel.id),
                )
                .where(CampaignRecipientModel.campaign_id == campaign_id)
                .group_by(
                    CampaignRecipientModel.ab_test_sampled,
                    CampaignRecipientModel.status,
                )
            )
        ).all()
        sampled = 0
        holdout_remaining = 0
        holdout_released = 0
        for is_sampled, status, count in rows:
            count = int(count)
            if is_sampled:
                sampled += count
            elif status == "holdout":
                holdout_remaining += count
            else:
                holdout_released += count
        return {
            "sampled_recipient_count": sampled,
            "holdout_recipient_count": holdout_remaining,
            "released_recipient_count": holdout_released,
        }

    async def get_or_create_message(
        self,
        *,
        campaign: CampaignModel,
        recipient: CampaignRecipientModel,
        step_order: int,
        sequence_step_id: int | None,
        ab_variant_id: int | None,
        idempotency_key: str,
    ) -> tuple[CampaignMessageModel, bool]:
        existing = (
            await self.session.execute(
                select(CampaignMessageModel).where(
                    CampaignMessageModel.idempotency_key == idempotency_key
                )
            )
        ).scalar_one_or_none()
        if existing:
            return existing, False
        message = CampaignMessageModel(
            organization_id=campaign.organization_id,
            campaign_id=campaign.id,
            recipient_id=recipient.id,
            sequence_step_id=sequence_step_id,
            ab_variant_id=ab_variant_id,
            step_order=step_order,
            idempotency_key=idempotency_key,
        )
        self.session.add(message)
        await self.session.flush()
        return message, True

    async def get_message_for_event(
        self,
        *,
        recipient_id: int,
        provider_message_id: str | None,
    ) -> CampaignMessageModel | None:
        stmt = select(CampaignMessageModel).where(
            CampaignMessageModel.recipient_id == recipient_id
        )
        if provider_message_id:
            stmt = stmt.where(
                CampaignMessageModel.provider_message_id == provider_message_id
            )
        stmt = stmt.order_by(CampaignMessageModel.id.desc()).limit(1)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_event_by_dedupe_key(
        self, dedupe_key: str
    ) -> CampaignMessageEventModel | None:
        return (
            await self.session.execute(
                select(CampaignMessageEventModel).where(
                    CampaignMessageEventModel.dedupe_key == dedupe_key
                )
            )
        ).scalar_one_or_none()

    async def add_event(self, event: CampaignMessageEventModel) -> None:
        self.session.add(event)
        await self.session.flush()

    async def count_sent_messages_since(
        self, campaign_id: int, since_utc: datetime
    ) -> int:
        return int(
            (
                await self.session.execute(
                    select(func.count(CampaignMessageModel.id)).where(
                        CampaignMessageModel.campaign_id == campaign_id,
                        CampaignMessageModel.status == "sent",
                        CampaignMessageModel.sent_at >= since_utc,
                    )
                )
            ).scalar()
            or 0
        )

    async def suppressed_emails(
        self, organization_id: int, normalized_emails: list[str]
    ) -> set[str]:
        if not normalized_emails:
            return set()
        rows = (
            await self.session.execute(
                select(CampaignSuppressionModel.normalized_email).where(
                    CampaignSuppressionModel.organization_id == organization_id,
                    CampaignSuppressionModel.active.is_(True),
                    CampaignSuppressionModel.normalized_email.in_(normalized_emails),
                )
            )
        ).scalars().all()
        return set(rows)

    async def is_suppressed(self, organization_id: int, normalized_email: str) -> bool:
        return bool(
            (
                await self.session.execute(
                    select(CampaignSuppressionModel.id).where(
                        CampaignSuppressionModel.organization_id == organization_id,
                        CampaignSuppressionModel.normalized_email == normalized_email,
                        CampaignSuppressionModel.active.is_(True),
                    )
                )
            ).scalar_one_or_none()
        )

    async def suppress_email(
        self,
        *,
        organization_id: int,
        normalized_email: str,
        reason: str,
        campaign_id: int,
        recipient_id: int,
        suppressed_at: datetime,
    ) -> CampaignSuppressionModel:
        existing = (
            await self.session.execute(
                select(CampaignSuppressionModel).where(
                    CampaignSuppressionModel.organization_id == organization_id,
                    CampaignSuppressionModel.normalized_email == normalized_email,
                )
            )
        ).scalar_one_or_none()
        if existing:
            existing.reason = reason
            existing.source_campaign_id = campaign_id
            existing.source_recipient_id = recipient_id
            existing.active = True
            existing.suppressed_at = suppressed_at
            existing.updated_at = suppressed_at
            suppression = existing
        else:
            suppression = CampaignSuppressionModel(
                organization_id=organization_id,
                normalized_email=normalized_email,
                reason=reason,
                source_campaign_id=campaign_id,
                source_recipient_id=recipient_id,
                active=True,
                suppressed_at=suppressed_at,
            )
            self.session.add(suppression)
        await self.session.flush()
        return suppression
