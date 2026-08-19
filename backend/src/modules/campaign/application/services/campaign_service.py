from __future__ import annotations

import hashlib
from datetime import UTC, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.campaign.domain.enums import (
    ABTestStatus,
    CampaignStatus,
    CampaignType,
    DelayUnit,
    RecipientStatus,
    ScheduleType,
    SequenceStatus,
    SequenceStepType,
)
from src.modules.campaign.domain.services import (
    build_event_dedupe_key,
    build_message_idempotency_key,
    choose_ab_variant,
    campaign_contact_ineligibility_reason,
    is_ab_test_sample_recipient,
    is_ab_winner_ready,
    is_uncertain_send_exception,
    is_within_sending_window,
    next_sending_window_at,
    normalize_email,
    validate_campaign_type_configuration,
    validate_sending_window,
    validate_sequence_steps,
    validate_timezone_name,
)
from src.modules.campaign.infrastructure.models import (
    CampaignABTestModel,
    CampaignABVariantModel,
    CampaignMessageEventModel,
    CampaignMessageModel,
    CampaignModel,
    CampaignRecipientModel,
    CampaignSequenceModel,
    CampaignSequenceStepModel,
)
from src.modules.campaign.infrastructure.repositories import CampaignRepositoryImpl
from src.modules.email_template.domain.services.template_rendering_service import (
    TemplateRenderingService,
)
from src.modules.platform.application.unsubscribe import unsubscribe_url
from src.shared.exceptions.base_exceptions import (
    ConflictError,
    InvalidError,
    NotFoundError,
)

_EDITABLE_STATUSES = {
    CampaignStatus.DRAFT.value,
    CampaignStatus.READY.value,
    CampaignStatus.FAILED.value,
}
_TERMINAL_RECIPIENT_STATUSES = {
    RecipientStatus.SENT.value,
    RecipientStatus.DELIVERED.value,
    RecipientStatus.OPENED.value,
    RecipientStatus.CLICKED.value,
    RecipientStatus.REPLIED.value,
    RecipientStatus.BOUNCED.value,
    RecipientStatus.FAILED.value,
    RecipientStatus.UNSUBSCRIBED.value,
    RecipientStatus.SKIPPED.value,
    RecipientStatus.STOPPED.value,
}

_ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    CampaignStatus.DRAFT.value: {
        CampaignStatus.READY.value,
        CampaignStatus.CANCELLED.value,
        CampaignStatus.ARCHIVED.value,
    },
    CampaignStatus.READY.value: {
        CampaignStatus.DRAFT.value,
        CampaignStatus.SCHEDULED.value,
        CampaignStatus.LAUNCHING.value,
        CampaignStatus.CANCELLED.value,
        CampaignStatus.ARCHIVED.value,
    },
    CampaignStatus.SCHEDULED.value: {
        CampaignStatus.LAUNCHING.value,
        CampaignStatus.CANCELLED.value,
        CampaignStatus.ARCHIVED.value,
    },
    CampaignStatus.LAUNCHING.value: {
        CampaignStatus.RUNNING.value,
        CampaignStatus.FAILED.value,
        CampaignStatus.CANCELLED.value,
    },
    CampaignStatus.RUNNING.value: {
        CampaignStatus.PAUSED.value,
        CampaignStatus.COMPLETED.value,
        CampaignStatus.FAILED.value,
        CampaignStatus.CANCELLED.value,
    },
    CampaignStatus.PAUSED.value: {
        CampaignStatus.RUNNING.value,
        CampaignStatus.CANCELLED.value,
    },
    CampaignStatus.COMPLETED.value: {CampaignStatus.ARCHIVED.value},
    CampaignStatus.CANCELLED.value: {CampaignStatus.ARCHIVED.value},
    CampaignStatus.FAILED.value: {
        CampaignStatus.DRAFT.value,
        CampaignStatus.READY.value,
        CampaignStatus.LAUNCHING.value,
        CampaignStatus.ARCHIVED.value,
    },
    CampaignStatus.ARCHIVED.value: set(),
}


class UncertainSendOutcomeError(RuntimeError):
    """Raised when the provider may have accepted a message but did not confirm it."""


class CampaignService:
    """Application service coordinating Campaign and existing MailTracko modules."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = CampaignRepositoryImpl(session)
        self.rendering_service = TemplateRenderingService()

    async def create_campaign(
        self,
        *,
        organization_id: int,
        actor_id: int,
        payload,
    ) -> dict[str, Any]:
        email_account = await self._resolve_email_account(
            payload.email_account_uuid, organization_id
        )
        template = await self._resolve_template(payload.template_uuid, organization_id)
        contact_list = await self._resolve_contact_list(
            payload.contact_list_uuid, organization_id
        )

        campaign = CampaignModel(
            organization_id=organization_id,
            created_by_id=actor_id,
            name=payload.name.strip(),
            description=payload.description,
            campaign_type=payload.campaign_type.value,
            goal=payload.goal.value,
            priority=payload.priority.value,
            timezone=validate_timezone_name(payload.timezone),
            sending_window_start=payload.sending_window_start,
            sending_window_end=payload.sending_window_end,
            sending_days=validate_sending_window(
                payload.sending_window_start,
                payload.sending_window_end,
                payload.sending_days,
            ),
            email_account_id=email_account["id"] if email_account else None,
            template_id=template["id"] if template else None,
            contact_list_id=contact_list["id"] if contact_list else None,
            daily_limit=payload.daily_limit,
            batch_size=payload.batch_size,
        )
        await self.repository.add_campaign(campaign)
        return await self.campaign_view(campaign)

    async def update_campaign(
        self,
        *,
        campaign: CampaignModel,
        organization_id: int,
        actor_id: int,
        payload,
    ) -> dict[str, Any]:
        self._ensure_editable(campaign)
        changed_references = False
        fields = payload.model_fields_set
        launch_affecting_fields = {
            "timezone",
            "sending_window_start",
            "sending_window_end",
            "sending_days",
            "daily_limit",
            "batch_size",
            "email_account_uuid",
            "template_uuid",
            "contact_list_uuid",
        }

        if "name" in fields and payload.name is not None:
            campaign.name = payload.name.strip()
        if "description" in fields:
            campaign.description = (
                payload.description.strip() if payload.description else None
            )
        if "goal" in fields and payload.goal is not None:
            campaign.goal = payload.goal.value
        if "priority" in fields and payload.priority is not None:
            campaign.priority = payload.priority.value
        if "current_step" in fields and payload.current_step is not None:
            campaign.current_step = payload.current_step.value
        if "timezone" in fields and payload.timezone is not None:
            campaign.timezone = validate_timezone_name(payload.timezone)
        if "sending_window_start" in fields:
            campaign.sending_window_start = payload.sending_window_start
        if "sending_window_end" in fields:
            campaign.sending_window_end = payload.sending_window_end
        if "sending_days" in fields and payload.sending_days is not None:
            campaign.sending_days = payload.sending_days
        if "daily_limit" in fields:
            campaign.daily_limit = payload.daily_limit
        if "batch_size" in fields and payload.batch_size is not None:
            campaign.batch_size = payload.batch_size

        campaign.sending_days = validate_sending_window(
            campaign.sending_window_start,
            campaign.sending_window_end,
            campaign.sending_days,
        )

        if "email_account_uuid" in fields:
            account = await self._resolve_email_account(
                payload.email_account_uuid, organization_id
            )
            campaign.email_account_id = account["id"] if account else None
            changed_references = True
        if "template_uuid" in fields:
            template = await self._resolve_template(
                payload.template_uuid, organization_id
            )
            campaign.template_id = template["id"] if template else None
            changed_references = True
        if "contact_list_uuid" in fields:
            contact_list = await self._resolve_contact_list(
                payload.contact_list_uuid, organization_id
            )
            campaign.contact_list_id = contact_list["id"] if contact_list else None
            changed_references = True

        if changed_references:
            await self.repository.delete_recipients(campaign.id)
            self._reset_counters(campaign)

        if fields & launch_affecting_fields:
            await self._transition_campaign(
                campaign,
                CampaignStatus.DRAFT.value,
                actor_id=actor_id,
                reason="Campaign launch configuration changed",
            )

        campaign.updated_by_id = actor_id
        campaign.updated_at = datetime.now(UTC)
        await self.session.flush()
        return await self.campaign_view(campaign)

    async def duplicate_campaign(
        self,
        *,
        campaign: CampaignModel,
        actor_id: int,
    ) -> dict[str, Any]:
        duplicate = CampaignModel(
            organization_id=campaign.organization_id,
            created_by_id=actor_id,
            name=f"{campaign.name} Copy"[:150],
            description=campaign.description,
            campaign_type=campaign.campaign_type,
            goal=campaign.goal,
            priority=campaign.priority,
            status=CampaignStatus.DRAFT.value,
            current_step=campaign.current_step,
            email_account_id=campaign.email_account_id,
            template_id=campaign.template_id,
            contact_list_id=campaign.contact_list_id,
            schedule_type=ScheduleType.IMMEDIATE.value,
            timezone=campaign.timezone,
            sending_window_start=campaign.sending_window_start,
            sending_window_end=campaign.sending_window_end,
            sending_days=list(campaign.sending_days or range(7)),
            daily_limit=campaign.daily_limit,
            batch_size=campaign.batch_size,
        )
        await self.repository.add_campaign(duplicate)

        if campaign.campaign_type == CampaignType.SEQUENCE.value:
            sequence, steps = await self.repository.get_sequence(campaign.id)
            if sequence:
                step_dicts = [self._sequence_step_copy_dict(step) for step in steps]
                await self.repository.replace_sequence(
                    campaign_id=duplicate.id,
                    organization_id=duplicate.organization_id,
                    stop_on_reply=sequence.stop_on_reply,
                    stop_on_unsubscribe=sequence.stop_on_unsubscribe,
                    stop_on_click=sequence.stop_on_click,
                    stop_on_meeting=sequence.stop_on_meeting,
                    custom_stop_events=list(sequence.custom_stop_events or []),
                    steps=step_dicts,
                )
        elif campaign.campaign_type == CampaignType.AB_TEST.value:
            ab_test, variants = await self.repository.get_ab_test(campaign.id)
            if ab_test:
                await self.repository.replace_ab_test(
                    campaign_id=duplicate.id,
                    organization_id=duplicate.organization_id,
                    test_percentage=ab_test.test_percentage,
                    winner_metric=ab_test.winner_metric,
                    auto_select_winner=ab_test.auto_select_winner,
                    minimum_sample_size=ab_test.minimum_sample_size,
                    test_duration_hours=ab_test.test_duration_hours,
                    variants=[self._ab_variant_copy_dict(v) for v in variants],
                )
        return await self.campaign_view(duplicate)

    async def configure_sequence(
        self,
        *,
        campaign: CampaignModel,
        organization_id: int,
        actor_id: int,
        payload,
    ) -> dict[str, Any]:
        self._ensure_editable(campaign)
        if campaign.campaign_type != CampaignType.SEQUENCE.value:
            raise InvalidError(error="Only sequence campaigns can have sequence steps")

        step_dicts: list[dict[str, Any]] = []
        for step in payload.steps:
            template = await self._resolve_template(step.template_uuid, organization_id)
            step_dicts.append(
                {
                    "step_order": step.step_order,
                    "step_type": step.step_type.value,
                    "template_id": template["id"] if template else None,
                    "subject_override": step.subject_override,
                    "body_html_override": step.body_html_override,
                    "delay_value": step.delay_value,
                    "delay_unit": step.delay_unit.value if step.delay_unit else None,
                    "is_enabled": step.is_enabled,
                }
            )
        validate_sequence_steps(step_dicts)
        sequence, steps = await self.repository.replace_sequence(
            campaign_id=campaign.id,
            organization_id=organization_id,
            stop_on_reply=payload.stop_on_reply,
            stop_on_unsubscribe=payload.stop_on_unsubscribe,
            stop_on_click=payload.stop_on_click,
            stop_on_meeting=payload.stop_on_meeting,
            custom_stop_events=payload.custom_stop_events,
            steps=step_dicts,
        )
        campaign.updated_by_id = actor_id
        campaign.current_step = "content"
        await self._transition_campaign(
            campaign,
            CampaignStatus.DRAFT.value,
            actor_id=actor_id,
            reason="Sequence configuration changed",
        )
        campaign.updated_at = datetime.now(UTC)
        await self.repository.delete_recipients(campaign.id)
        self._reset_counters(campaign)
        await self.session.flush()
        return await self.sequence_view(sequence, steps)

    async def configure_ab_test(
        self,
        *,
        campaign: CampaignModel,
        organization_id: int,
        actor_id: int,
        payload,
    ) -> dict[str, Any]:
        self._ensure_editable(campaign)
        if campaign.campaign_type != CampaignType.AB_TEST.value:
            raise InvalidError(error="Only A/B test campaigns can have variants")

        variants: list[dict[str, Any]] = []
        for variant in payload.variants:
            template = await self._resolve_template(
                variant.template_uuid, organization_id
            )
            variants.append(
                {
                    "variant_type": variant.variant_type.value,
                    "name": variant.name.strip(),
                    "template_id": template["id"] if template else None,
                    "subject_override": variant.subject_override,
                    "body_html_override": variant.body_html_override,
                    "allocation_percentage": variant.allocation_percentage,
                }
            )
        choose_ab_variant("configuration-check@mailtracko.invalid", variants)
        ab_test, models = await self.repository.replace_ab_test(
            campaign_id=campaign.id,
            organization_id=organization_id,
            test_percentage=payload.test_percentage,
            winner_metric=payload.winner_metric,
            auto_select_winner=payload.auto_select_winner,
            minimum_sample_size=payload.minimum_sample_size,
            test_duration_hours=payload.test_duration_hours,
            variants=variants,
        )
        campaign.updated_by_id = actor_id
        campaign.current_step = "content"
        await self._transition_campaign(
            campaign,
            CampaignStatus.DRAFT.value,
            actor_id=actor_id,
            reason="A/B test configuration changed",
        )
        campaign.updated_at = datetime.now(UTC)
        await self.repository.delete_recipients(campaign.id)
        self._reset_counters(campaign)
        await self.session.flush()
        return await self.ab_test_view(ab_test, models)

    async def review_campaign(
        self, campaign: CampaignModel, *, actor_id: int | None = None
    ) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []

        try:
            campaign.timezone = validate_timezone_name(campaign.timezone)
            campaign.sending_days = validate_sending_window(
                campaign.sending_window_start,
                campaign.sending_window_end,
                campaign.sending_days,
            )
        except ValueError as exc:
            errors.append(str(exc))

        account = await self._get_email_account_by_id(
            campaign.email_account_id, campaign.organization_id
        )
        if not account:
            errors.append("Select a sender account")
        elif account["status"] != "active":
            errors.append("The selected sender account is not active")
        elif account.get("health_status") == "unhealthy":
            warnings.append("The selected sender account is unhealthy")

        contact_list = await self._get_contact_list_by_id(
            campaign.contact_list_id, campaign.organization_id
        )
        if not contact_list:
            errors.append("Select a valid contact list")

        sequence, steps = await self.repository.get_sequence(campaign.id)
        ab_test, variants = await self.repository.get_ab_test(campaign.id)
        try:
            validate_campaign_type_configuration(
                campaign_type=campaign.campaign_type,
                template_id=campaign.template_id,
                sequence_steps=[self._sequence_step_copy_dict(s) for s in steps],
                variants=[self._ab_variant_copy_dict(v) for v in variants],
            )
        except ValueError as exc:
            errors.append(str(exc))

        if campaign.template_id is not None:
            template = await self._get_template_by_id(
                campaign.template_id, campaign.organization_id
            )
            if not template:
                errors.append("The selected template is unavailable")
            elif template.get("status") == "archived":
                errors.append("The selected template is archived")

        errors.extend(
            await self._content_validation_errors(
                campaign=campaign,
                steps=steps,
                variants=variants,
            )
        )

        audience = await self._audience_preview(campaign)
        if audience["eligible"] == 0:
            errors.append("The selected contact list has no eligible recipients")
        if audience["excluded"]:
            warnings.append(
                f"{audience['excluded']} unsubscribed or invalid contacts will be excluded"
            )
        if audience["duplicates"]:
            warnings.append(
                f"{audience['duplicates']} duplicate email addresses will be removed"
            )
        if (
            campaign.campaign_type == CampaignType.AB_TEST.value
            and ab_test
            and ab_test.minimum_sample_size > audience.get("ab_sampled", 0)
        ):
            errors.append(
                "A/B minimum_sample_size exceeds the deterministic test sample "
                f"({audience.get('ab_sampled', 0)} recipients)"
            )

        ready = not errors
        if ready and campaign.status in {
            CampaignStatus.DRAFT.value,
            CampaignStatus.FAILED.value,
        }:
            await self._transition_campaign(
                campaign,
                CampaignStatus.READY.value,
                actor_id=actor_id,
                reason="Pre-send review passed",
            )
            campaign.current_step = "review"
            await self.session.flush()

        return {
            "ready": ready,
            "errors": errors,
            "warnings": warnings,
            "audience": audience,
        }

    async def schedule_campaign(
        self,
        *,
        campaign: CampaignModel,
        actor_id: int,
        scheduled_at: datetime,
        timezone: str,
    ) -> dict[str, Any]:
        if scheduled_at.tzinfo is None:
            raise InvalidError(error="scheduled_at must include a timezone offset")
        if scheduled_at.astimezone(UTC) <= datetime.now(UTC):
            raise InvalidError(error="scheduled_at must be in the future")
        timezone = validate_timezone_name(timezone)
        if not is_within_sending_window(
            scheduled_at.astimezone(UTC),
            timezone_name=timezone,
            start=campaign.sending_window_start,
            end=campaign.sending_window_end,
            days=campaign.sending_days,
        ):
            raise InvalidError(
                error="scheduled_at must fall inside the campaign sending window"
            )
        review = await self.review_campaign(campaign, actor_id=actor_id)
        if not review["ready"]:
            raise InvalidError(error="Campaign is not ready", errors=review)
        await self._snapshot_recipients(campaign)
        campaign.schedule_type = ScheduleType.ONE_TIME.value
        campaign.scheduled_at = scheduled_at.astimezone(UTC)
        campaign.timezone = timezone
        await self._transition_campaign(
            campaign,
            CampaignStatus.SCHEDULED.value,
            actor_id=actor_id,
            reason="Campaign scheduled",
        )
        campaign.updated_by_id = actor_id
        await self.session.flush()
        return await self.campaign_view(campaign)

    async def launch_campaign(
        self,
        *,
        campaign: CampaignModel,
        actor_id: int,
    ) -> dict[str, Any]:
        if campaign.status not in _EDITABLE_STATUSES | {CampaignStatus.SCHEDULED.value}:
            raise ConflictError(
                error=f"Campaign cannot launch while status is '{campaign.status}'"
            )
        review = await self.review_campaign(campaign, actor_id=actor_id)
        if not review["ready"]:
            raise InvalidError(error="Campaign is not ready", errors=review)
        if campaign.total_recipients <= 0:
            await self._snapshot_recipients(campaign)
        now = datetime.now(UTC)
        await self._transition_campaign(
            campaign,
            CampaignStatus.LAUNCHING.value,
            actor_id=actor_id,
            reason="Campaign launch requested",
        )
        await self._transition_campaign(
            campaign,
            CampaignStatus.RUNNING.value,
            actor_id=actor_id,
            reason="Campaign launch started",
        )
        campaign.schedule_type = ScheduleType.IMMEDIATE.value
        campaign.scheduled_at = None
        campaign.updated_by_id = actor_id

        if campaign.campaign_type == CampaignType.SEQUENCE.value:
            sequence, _ = await self.repository.get_sequence(campaign.id)
            if sequence:
                sequence.status = SequenceStatus.ACTIVE.value
                sequence.updated_at = now
        elif campaign.campaign_type == CampaignType.AB_TEST.value:
            ab_test, _ = await self.repository.get_ab_test(campaign.id)
            if ab_test:
                ab_test.status = ABTestStatus.RUNNING.value
                ab_test.started_at = ab_test.started_at or now
                ab_test.updated_at = now
        await self.session.flush()
        return await self.campaign_view(campaign)

    async def pause_campaign(
        self, *, campaign: CampaignModel, actor_id: int
    ) -> dict[str, Any]:
        if campaign.status != CampaignStatus.RUNNING.value:
            raise ConflictError(error="Only a running campaign can be paused")
        await self._transition_campaign(
            campaign,
            CampaignStatus.PAUSED.value,
            actor_id=actor_id,
            reason="Campaign paused",
        )
        campaign.updated_by_id = actor_id
        sequence, _ = await self.repository.get_sequence(campaign.id)
        if sequence:
            sequence.status = SequenceStatus.PAUSED.value
            sequence.updated_at = campaign.updated_at
        await self.session.flush()
        return await self.campaign_view(campaign)

    async def resume_campaign(
        self, *, campaign: CampaignModel, actor_id: int
    ) -> dict[str, Any]:
        if campaign.status != CampaignStatus.PAUSED.value:
            raise ConflictError(error="Only a paused campaign can be resumed")
        review = await self.review_campaign(campaign, actor_id=actor_id)
        if not review["ready"]:
            raise InvalidError(
                error="Campaign cannot resume until its configuration is valid",
                errors=review,
            )
        await self._transition_campaign(
            campaign,
            CampaignStatus.RUNNING.value,
            actor_id=actor_id,
            reason="Campaign resumed",
        )
        campaign.updated_by_id = actor_id
        sequence, _ = await self.repository.get_sequence(campaign.id)
        if sequence:
            sequence.status = SequenceStatus.ACTIVE.value
            sequence.updated_at = campaign.updated_at
        await self.session.flush()
        return await self.campaign_view(campaign)

    async def cancel_campaign(
        self, *, campaign: CampaignModel, actor_id: int
    ) -> dict[str, Any]:
        if campaign.status in {
            CampaignStatus.COMPLETED.value,
            CampaignStatus.CANCELLED.value,
            CampaignStatus.ARCHIVED.value,
        }:
            raise ConflictError(error=f"Campaign is already {campaign.status}")
        now = datetime.now(UTC)
        await self._transition_campaign(
            campaign,
            CampaignStatus.CANCELLED.value,
            actor_id=actor_id,
            reason="Campaign cancelled",
        )
        campaign.updated_by_id = actor_id
        await self.session.execute(
            text(
                "UPDATE campaign_recipients SET status = 'skipped', "
                "stop_reason = 'campaign_cancelled', stopped_at = :now, "
                "next_attempt_at = NULL, updated_at = :now "
                "WHERE campaign_id = :campaign_id AND status NOT IN "
                "('sent','delivered','opened','clicked','replied','failed','bounced','unsubscribed','skipped','stopped')"
            ),
            {"now": now, "campaign_id": campaign.id},
        )
        sequence, _ = await self.repository.get_sequence(campaign.id)
        if sequence:
            sequence.status = SequenceStatus.STOPPED.value
            sequence.updated_at = now
        await self.session.flush()
        await self._refresh_counters(campaign, actor_id=actor_id)
        return await self.campaign_view(campaign)

    async def archive_campaign(
        self, *, campaign: CampaignModel, actor_id: int
    ) -> dict[str, Any]:
        if campaign.status in {
            CampaignStatus.RUNNING.value,
            CampaignStatus.LAUNCHING.value,
        }:
            raise ConflictError(error="Stop the campaign before archiving it")
        await self._transition_campaign(
            campaign,
            CampaignStatus.ARCHIVED.value,
            actor_id=actor_id,
            reason="Campaign archived",
        )
        campaign.updated_by_id = actor_id
        await self.session.flush()
        return await self.campaign_view(campaign)

    async def restore_campaign(
        self, *, campaign: CampaignModel, actor_id: int
    ) -> dict[str, Any]:
        if campaign.status != CampaignStatus.ARCHIVED.value:
            raise ConflictError(error="Only archived campaigns can be restored")

        now = datetime.now(UTC)
        restored_status = (
            CampaignStatus.COMPLETED.value
            if campaign.completed_at is not None
            else CampaignStatus.CANCELLED.value
            if campaign.cancelled_at is not None
            else CampaignStatus.DRAFT.value
        )
        previous_status = campaign.status
        campaign.status = restored_status
        campaign.archived_at = None
        campaign.updated_at = now
        campaign.updated_by_id = actor_id
        await self.repository.add_state_history(
            campaign=campaign,
            from_status=previous_status,
            to_status=restored_status,
            actor_id=actor_id,
            reason="Campaign restored from archive",
            transitioned_at=now,
        )
        await self.session.flush()
        return await self.campaign_view(campaign)

    async def delete_campaign(
        self, *, campaign: CampaignModel, actor_id: int
    ) -> dict[str, Any]:
        if campaign.status in {
            CampaignStatus.RUNNING.value,
            CampaignStatus.LAUNCHING.value,
        }:
            raise ConflictError(error="Stop the campaign before deleting it")

        now = datetime.now(UTC)
        if campaign.status == CampaignStatus.SCHEDULED.value:
            await self._transition_campaign(
                campaign,
                CampaignStatus.CANCELLED.value,
                actor_id=actor_id,
                reason="Scheduled campaign deleted",
            )

        campaign.deleted_at = now
        campaign.updated_at = now
        campaign.updated_by_id = actor_id

        sequence, _ = await self.repository.get_sequence(campaign.id)
        if sequence and sequence.status != SequenceStatus.STOPPED.value:
            sequence.status = SequenceStatus.STOPPED.value
            sequence.updated_at = now

        await self.session.flush()
        return await self.campaign_view(campaign)

    async def process_campaign(
        self,
        *,
        campaign: CampaignModel,
        actor_id: int,
        dry_run: bool,
        limit: int | None,
    ) -> dict[str, Any]:
        if campaign.status == CampaignStatus.SCHEDULED.value:
            if not campaign.scheduled_at or campaign.scheduled_at > datetime.now(UTC):
                raise ConflictError(error="Campaign is scheduled for a future time")
            await self.launch_campaign(campaign=campaign, actor_id=actor_id)
        if campaign.status != CampaignStatus.RUNNING.value:
            raise ConflictError(error="Only a running campaign can be processed")

        now = datetime.now(UTC)
        if not is_within_sending_window(
            now,
            timezone_name=campaign.timezone,
            start=campaign.sending_window_start,
            end=campaign.sending_window_end,
            days=campaign.sending_days,
        ):
            next_attempt_at = next_sending_window_at(
                now,
                timezone_name=campaign.timezone,
                start=campaign.sending_window_start,
                end=campaign.sending_window_end,
                days=campaign.sending_days,
            )
            deferred = 0
            if not dry_run:
                deferred = await self.repository.defer_due_recipients(
                    campaign.id, next_attempt_at=next_attempt_at
                )
            return {
                "dry_run": dry_run,
                "processed": 0,
                "sent": 0,
                "failed": 0,
                "deferred": deferred,
                "completed": False,
                "details": [
                    {
                        "outcome": "deferred",
                        "reason": "outside_sending_window",
                        "next_attempt_at": next_attempt_at.isoformat(),
                    }
                ],
            }

        account = await self._get_email_account_by_id(
            campaign.email_account_id, campaign.organization_id
        )
        if not account or account.get("status") != "active":
            raise InvalidError(
                error="Campaign sender account is unavailable or inactive"
            )

        batch_limit = min(limit or campaign.batch_size, campaign.batch_size)
        if campaign.daily_limit:
            sent_today = await self.repository.count_sent_messages_since(
                campaign.id, self._campaign_local_day_start(campaign, now)
            )
            batch_limit = min(batch_limit, max(campaign.daily_limit - sent_today, 0))
        if account.get("sending_limit") is not None:
            account_remaining = max(
                int(account["sending_limit"])
                - int(account.get("daily_sent_count") or 0),
                0,
            )
            batch_limit = min(batch_limit, account_remaining)
        if batch_limit <= 0:
            next_attempt_at = self._next_local_day_start(campaign, now)
            deferred = 0
            if not dry_run:
                deferred = await self.repository.defer_due_recipients(
                    campaign.id, next_attempt_at=next_attempt_at
                )
            return {
                "dry_run": dry_run,
                "processed": 0,
                "sent": 0,
                "failed": 0,
                "deferred": deferred,
                "completed": False,
                "details": [
                    {
                        "outcome": "deferred",
                        "reason": "daily_limit_reached",
                        "next_attempt_at": next_attempt_at.isoformat(),
                    }
                ],
            }
        recipients = await self.repository.list_due_recipients(
            campaign.id, limit=batch_limit
        )

        sequence, steps = await self.repository.get_sequence(campaign.id)
        ab_test, variants = await self.repository.get_ab_test(campaign.id)
        step_map = {step.step_order: step for step in steps}
        variant_map = {variant.id: variant for variant in variants}
        result = {
            "dry_run": dry_run,
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "deferred": 0,
            "skipped": 0,
            "completed": False,
            "details": [],
        }

        for recipient in recipients:
            result["processed"] += 1
            eligibility_reason = await self._recipient_ineligibility_reason(recipient)
            if eligibility_reason:
                if not dry_run:
                    recipient.status = RecipientStatus.SKIPPED.value
                    recipient.stop_reason = eligibility_reason
                    recipient.stopped_at = datetime.now(UTC)
                    recipient.next_attempt_at = None
                    recipient.updated_at = recipient.stopped_at
                result["skipped"] += 1
                result["details"].append(
                    {
                        "recipient_uuid": recipient.uuid,
                        "email": recipient.email,
                        "outcome": "skipped",
                        "status": recipient.status,
                        "reason": eligibility_reason,
                    }
                )
                continue
            if not dry_run:
                recipient.attempt_count += 1
                recipient.updated_at = datetime.now(UTC)
            try:
                if campaign.campaign_type == CampaignType.SEQUENCE.value:
                    outcome = await self._process_sequence_recipient(
                        campaign=campaign,
                        recipient=recipient,
                        steps=step_map,
                        account=account,
                        actor_id=actor_id,
                        dry_run=dry_run,
                    )
                else:
                    variant = variant_map.get(recipient.ab_variant_id)
                    outcome = await self._process_single_recipient(
                        campaign=campaign,
                        recipient=recipient,
                        account=account,
                        actor_id=actor_id,
                        dry_run=dry_run,
                        variant=variant,
                    )
                result[outcome] += 1
                result["details"].append(
                    {
                        "recipient_uuid": recipient.uuid,
                        "email": recipient.email,
                        "outcome": outcome,
                        "status": recipient.status,
                    }
                )
            except UncertainSendOutcomeError as exc:
                result["failed"] += 1
                result["details"].append(
                    {
                        "recipient_uuid": recipient.uuid,
                        "email": recipient.email,
                        "outcome": "failed",
                        "status": recipient.status,
                        "error": str(exc),
                        "error_code": "SEND_OUTCOME_UNCERTAIN",
                    }
                )
            except Exception as exc:
                outcome = (
                    "deferred"
                    if dry_run
                    else self._record_send_failure(recipient, str(exc))
                )
                if outcome == "failed":
                    result["failed"] += 1
                else:
                    result["deferred"] += 1
                variant = variant_map.get(recipient.ab_variant_id)
                if variant and recipient.ab_test_sampled and outcome == "failed":
                    variant.failed_count += 1
                    variant.updated_at = datetime.now(UTC)
                result["details"].append(
                    {
                        "recipient_uuid": recipient.uuid,
                        "email": recipient.email,
                        "outcome": outcome,
                        "status": recipient.status,
                        "error": str(exc),
                    }
                )

        await self.session.flush()
        if not dry_run:
            await self._refresh_counters(campaign, actor_id=actor_id)
            await self._maybe_select_ab_winner(campaign)
        result["completed"] = campaign.status == CampaignStatus.COMPLETED.value
        return result

    async def reconcile_send_outcome(
        self,
        *,
        campaign: CampaignModel,
        recipient_uuid: str,
        outcome: str,
        provider_message_id: str | None,
        provider_thread_id: str | None,
        actor_id: int,
    ) -> dict[str, Any]:
        recipient = await self.repository.get_recipient(recipient_uuid, campaign.id)
        if not recipient:
            raise NotFoundError(error="Campaign recipient not found")
        message = await self.repository.get_message_for_event(
            recipient_id=recipient.id, provider_message_id=None
        )
        if not message or message.status != "uncertain":
            raise ConflictError(
                error="The recipient has no uncertain send outcome to reconcile"
            )

        now = datetime.now(UTC)
        message.reconciled_at = now
        message.updated_at = now
        if provider_message_id:
            message.provider_message_id = provider_message_id
            recipient.provider_message_id = provider_message_id
        if provider_thread_id:
            message.provider_thread_id = provider_thread_id
            recipient.provider_thread_id = provider_thread_id

        if outcome == "sent":
            message.status = "sent"
            message.sent_at = message.sent_at or now
            message.last_error_code = None
            message.last_error_message = None
            recipient.last_error_code = None
            recipient.last_error_message = None
            recipient.failed_at = None
            recipient.sent_at = recipient.sent_at or now
            if campaign.campaign_type == CampaignType.SEQUENCE.value:
                _, sequence_steps = await self.repository.get_sequence(campaign.id)
                step_map = {step.step_order: step for step in sequence_steps}
                recipient.sequence_step_id = message.sequence_step_id
                recipient.attempt_count = 0
                self._advance_sequence_after_step(
                    recipient, step_map, message.step_order, now
                )
            else:
                recipient.status = RecipientStatus.SENT.value
                recipient.next_attempt_at = None
                recipient.updated_at = now
                if message.ab_variant_id:
                    variant = await self.session.get(
                        CampaignABVariantModel, message.ab_variant_id
                    )
                    if variant and recipient.ab_test_sampled:
                        variant.sent_count += 1
                        variant.updated_at = now
        elif outcome == "retry":
            message.status = "failed"
            message.last_error_code = "RECONCILED_FOR_RETRY"
            message.last_error_message = (
                "Provider confirmed the previous send was not accepted"
            )
            message.failed_at = now
            recipient.status = RecipientStatus.PENDING.value
            recipient.attempt_count = 0
            recipient.failed_at = None
            recipient.last_error_code = None
            recipient.last_error_message = None
            recipient.next_attempt_at = now
            recipient.updated_at = now
        else:
            message.status = "failed"
            message.last_error_code = "RECONCILED_FAILED"
            message.last_error_message = "Provider confirmed the send failed"
            message.failed_at = now
            recipient.status = RecipientStatus.FAILED.value
            recipient.last_error_code = "RECONCILED_FAILED"
            recipient.last_error_message = "Provider confirmed the send failed"
            recipient.failed_at = now
            recipient.next_attempt_at = None
            recipient.updated_at = now

        await self._refresh_counters(campaign, actor_id=actor_id)
        return self._recipient_to_dict(recipient)

    async def record_recipient_event(
        self,
        *,
        campaign: CampaignModel,
        recipient_uuid: str,
        event_type: str,
        provider_event_id: str | None,
        provider_message_id: str | None,
        custom_event_name: str | None,
        occurred_at: datetime | None,
        metadata: dict[str, Any] | None,
        actor_id: int | None,
    ) -> dict[str, Any]:
        recipient = await self.repository.get_recipient(recipient_uuid, campaign.id)
        if not recipient:
            raise NotFoundError(error="Campaign recipient not found")
        now = datetime.now(UTC)
        event_time = occurred_at or now
        if event_time.tzinfo is None:
            raise InvalidError(error="occurred_at must include timezone information")
        event_time = event_time.astimezone(UTC)
        dedupe_key = build_event_dedupe_key(
            campaign_uuid=campaign.uuid,
            recipient_uuid=recipient.uuid,
            event_type=event_type,
            provider_event_id=provider_event_id,
            provider_message_id=provider_message_id,
            custom_event_name=custom_event_name,
        )
        if await self.repository.get_event_by_dedupe_key(dedupe_key):
            return self._recipient_to_dict(recipient)

        message = await self.repository.get_message_for_event(
            recipient_id=recipient.id,
            provider_message_id=provider_message_id,
        )
        await self.repository.add_event(
            CampaignMessageEventModel(
                organization_id=campaign.organization_id,
                campaign_id=campaign.id,
                recipient_id=recipient.id,
                message_id=message.id if message else None,
                event_type=event_type,
                custom_event_name=custom_event_name,
                provider_event_id=provider_event_id,
                provider_message_id=provider_message_id,
                dedupe_key=dedupe_key,
                occurred_at=event_time,
                event_metadata=metadata,
            )
        )

        variant = None
        if recipient.ab_variant_id:
            variant = await self.session.get(
                CampaignABVariantModel, recipient.ab_variant_id
            )
        sequence, _ = await self.repository.get_sequence(campaign.id)
        is_active_sequence = (
            campaign.campaign_type == CampaignType.SEQUENCE.value
            and recipient.status
            in {
                RecipientStatus.PENDING.value,
                RecipientStatus.QUEUED.value,
                RecipientStatus.SENDING.value,
            }
        )
        timestamp_field = {
            "bounced": "bounced_at",
            "meeting": None,
            "custom": None,
        }.get(event_type, f"{event_type}_at")
        previous_value = (
            getattr(recipient, timestamp_field, None) if timestamp_field else None
        )

        should_stop_sequence = False
        stop_reason = None
        if event_type == "delivered":
            recipient.delivered_at = recipient.delivered_at or event_time
            if (
                not is_active_sequence
                and recipient.status == RecipientStatus.SENT.value
            ):
                recipient.status = RecipientStatus.DELIVERED.value
        elif event_type == "opened":
            recipient.opened_at = recipient.opened_at or event_time
            if not is_active_sequence and recipient.status not in {
                RecipientStatus.CLICKED.value,
                RecipientStatus.REPLIED.value,
            }:
                recipient.status = RecipientStatus.OPENED.value
        elif event_type == "clicked":
            recipient.clicked_at = recipient.clicked_at or event_time
            if is_active_sequence and sequence and sequence.stop_on_click:
                should_stop_sequence = True
                stop_reason = "clicked"
            elif (
                not is_active_sequence
                and recipient.status != RecipientStatus.REPLIED.value
            ):
                recipient.status = RecipientStatus.CLICKED.value
        elif event_type == "replied":
            recipient.replied_at = recipient.replied_at or event_time
            if not is_active_sequence or not sequence or sequence.stop_on_reply:
                recipient.status = RecipientStatus.REPLIED.value
                should_stop_sequence = is_active_sequence
                stop_reason = "replied"
        elif event_type == "bounced":
            recipient.status = RecipientStatus.BOUNCED.value
            recipient.bounced_at = recipient.bounced_at or event_time
            recipient.failed_at = recipient.failed_at or event_time
            should_stop_sequence = is_active_sequence
            stop_reason = "bounced"
            await self.repository.suppress_email(
                organization_id=campaign.organization_id,
                normalized_email=recipient.normalized_email,
                reason="bounced",
                campaign_id=campaign.id,
                recipient_id=recipient.id,
                suppressed_at=event_time,
            )
        elif event_type == "unsubscribed":
            recipient.status = RecipientStatus.UNSUBSCRIBED.value
            recipient.unsubscribed_at = recipient.unsubscribed_at or event_time
            should_stop_sequence = is_active_sequence
            stop_reason = "unsubscribed"
            await self.repository.suppress_email(
                organization_id=campaign.organization_id,
                normalized_email=recipient.normalized_email,
                reason="unsubscribed",
                campaign_id=campaign.id,
                recipient_id=recipient.id,
                suppressed_at=event_time,
            )
            if recipient.contact_id:
                await self.session.execute(
                    text(
                        "UPDATE contact_contacts SET subscribed = false, "
                        "unsubscribed_at = :now, updated_at = :now "
                        "WHERE id = :contact_id AND organization_id = :organization_id"
                    ),
                    {
                        "now": event_time,
                        "contact_id": recipient.contact_id,
                        "organization_id": campaign.organization_id,
                    },
                )
        elif event_type == "meeting":
            if is_active_sequence and sequence and sequence.stop_on_meeting:
                should_stop_sequence = True
                stop_reason = "meeting"
        elif event_type == "custom":
            if (
                is_active_sequence
                and sequence
                and custom_event_name in set(sequence.custom_stop_events or [])
            ):
                should_stop_sequence = True
                stop_reason = f"custom:{custom_event_name}"

        if should_stop_sequence:
            if event_type not in {"replied", "bounced", "unsubscribed"}:
                recipient.status = RecipientStatus.STOPPED.value
            recipient.stop_reason = stop_reason
            recipient.stopped_at = event_time
            recipient.next_attempt_at = None
        if provider_message_id:
            recipient.provider_message_id = provider_message_id
        recipient.updated_at = now

        if variant and recipient.ab_test_sampled and previous_value is None:
            counter_name = {
                "delivered": "delivered_count",
                "opened": "opened_count",
                "clicked": "clicked_count",
                "replied": "replied_count",
                "bounced": "failed_count",
            }.get(event_type)
            if counter_name:
                setattr(variant, counter_name, getattr(variant, counter_name) + 1)
                variant.updated_at = now

        await self.session.flush()
        await self._refresh_counters(campaign, actor_id=actor_id)
        await self._maybe_select_ab_winner(campaign)
        return self._recipient_to_dict(recipient)

    async def campaign_view(self, campaign: CampaignModel) -> dict[str, Any]:
        account = await self._get_email_account_by_id(
            campaign.email_account_id, campaign.organization_id
        )
        template = await self._get_template_by_id(
            campaign.template_id, campaign.organization_id
        )
        contact_list = await self._get_contact_list_by_id(
            campaign.contact_list_id, campaign.organization_id
        )
        total = campaign.total_recipients or 0
        terminal = campaign.sent_count + campaign.failed_count + campaign.skipped_count
        progress = round((terminal / total) * 100, 2) if total else 0.0
        return {
            "uuid": campaign.uuid,
            "organization_id": campaign.organization_id,
            "name": campaign.name,
            "description": campaign.description,
            "campaign_type": campaign.campaign_type,
            "goal": campaign.goal,
            "priority": campaign.priority,
            "status": campaign.status,
            "current_step": campaign.current_step,
            "email_account_uuid": account["uuid"] if account else None,
            "email_account_email": account["email"] if account else None,
            "template_uuid": template["uuid"] if template else None,
            "template_name": template["name"] if template else None,
            "contact_list_uuid": contact_list["uuid"] if contact_list else None,
            "contact_list_name": contact_list["name"] if contact_list else None,
            "schedule_type": campaign.schedule_type,
            "timezone": campaign.timezone,
            "scheduled_at": campaign.scheduled_at,
            "sending_window_start": campaign.sending_window_start,
            "sending_window_end": campaign.sending_window_end,
            "sending_days": list(campaign.sending_days or range(7)),
            "daily_limit": campaign.daily_limit,
            "batch_size": campaign.batch_size,
            "total_recipients": campaign.total_recipients,
            "sent_count": campaign.sent_count,
            "failed_count": campaign.failed_count,
            "skipped_count": campaign.skipped_count,
            "progress_percentage": progress,
            "launched_at": campaign.launched_at,
            "paused_at": campaign.paused_at,
            "completed_at": campaign.completed_at,
            "cancelled_at": campaign.cancelled_at,
            "archived_at": campaign.archived_at,
            "created_at": campaign.created_at,
            "updated_at": campaign.updated_at,
        }

    async def sequence_view(
        self,
        sequence: CampaignSequenceModel,
        steps: list[CampaignSequenceStepModel],
    ) -> dict[str, Any]:
        items = []
        for step in steps:
            template = await self._get_template_by_id(
                step.template_id, sequence.organization_id
            )
            items.append(
                {
                    "uuid": step.uuid,
                    "step_order": step.step_order,
                    "step_type": step.step_type,
                    "template_uuid": template["uuid"] if template else None,
                    "template_name": template["name"] if template else None,
                    "subject_override": step.subject_override,
                    "body_html_override": step.body_html_override,
                    "delay_value": step.delay_value,
                    "delay_unit": step.delay_unit,
                    "is_enabled": step.is_enabled,
                }
            )
        return {
            "uuid": sequence.uuid,
            "status": sequence.status,
            "stop_on_reply": sequence.stop_on_reply,
            "stop_on_unsubscribe": sequence.stop_on_unsubscribe,
            "stop_on_click": sequence.stop_on_click,
            "stop_on_meeting": sequence.stop_on_meeting,
            "custom_stop_events": list(sequence.custom_stop_events or []),
            "total_steps": sequence.total_steps,
            "steps": items,
        }

    async def ab_test_view(
        self,
        ab_test: CampaignABTestModel,
        variants: list[CampaignABVariantModel],
    ) -> dict[str, Any]:
        items = []
        winner_uuid = None
        for variant in variants:
            template = await self._get_template_by_id(
                variant.template_id, ab_test.organization_id
            )
            if variant.id == ab_test.winner_variant_id:
                winner_uuid = variant.uuid
            items.append(
                {
                    "uuid": variant.uuid,
                    "variant_type": variant.variant_type,
                    "name": variant.name,
                    "template_uuid": template["uuid"] if template else None,
                    "template_name": template["name"] if template else None,
                    "subject_override": variant.subject_override,
                    "body_html_override": variant.body_html_override,
                    "allocation_percentage": variant.allocation_percentage,
                    "sent_count": variant.sent_count,
                    "delivered_count": variant.delivered_count,
                    "opened_count": variant.opened_count,
                    "clicked_count": variant.clicked_count,
                    "replied_count": variant.replied_count,
                    "failed_count": variant.failed_count,
                }
            )
        audience_counts = await self.repository.ab_audience_counts(ab_test.campaign_id)
        return {
            "uuid": ab_test.uuid,
            "status": ab_test.status,
            "test_percentage": ab_test.test_percentage,
            "winner_metric": ab_test.winner_metric,
            "auto_select_winner": ab_test.auto_select_winner,
            "minimum_sample_size": ab_test.minimum_sample_size,
            "test_duration_hours": ab_test.test_duration_hours,
            "started_at": ab_test.started_at,
            "winner_selected_at": ab_test.winner_selected_at,
            "winner_variant_uuid": winner_uuid,
            **audience_counts,
            "variants": items,
        }

    async def select_ab_winner(
        self,
        *,
        campaign: CampaignModel,
        variant_type: str | None = None,
    ) -> dict[str, Any]:
        ab_test, variants = await self.repository.get_ab_test(campaign.id)
        if not ab_test or not variants:
            raise NotFoundError(error="A/B test configuration not found")
        if variant_type:
            winner = next((v for v in variants if v.variant_type == variant_type), None)
            if not winner:
                raise NotFoundError(error="A/B variant not found")
        else:
            metric_field = {
                "delivery_rate": "delivered_count",
                "open_rate": "opened_count",
                "click_rate": "clicked_count",
                "reply_rate": "replied_count",
            }[ab_test.winner_metric]
            winner = max(
                variants,
                key=lambda v: (
                    getattr(v, metric_field) / v.sent_count if v.sent_count else 0,
                    v.sent_count,
                    v.variant_type == "a",
                ),
            )
        ab_test.winner_variant_id = winner.id
        ab_test.status = ABTestStatus.WINNER_SELECTED.value
        ab_test.winner_selected_at = datetime.now(UTC)
        ab_test.updated_at = ab_test.winner_selected_at
        await self.repository.assign_pending_recipients_to_variant(
            campaign.id, winner.id
        )
        await self.session.flush()
        return await self.ab_test_view(ab_test, variants)

    async def sequence_preview(
        self,
        *,
        campaign: CampaignModel,
        starts_at: datetime | None,
    ) -> dict[str, Any]:
        if campaign.campaign_type != CampaignType.SEQUENCE.value:
            raise InvalidError(error="Only sequence campaigns have a sequence preview")
        sequence, steps = await self.repository.get_sequence(campaign.id)
        if not sequence or not steps:
            raise NotFoundError(error="Sequence configuration not found")
        start = starts_at or datetime.now(UTC)
        if start.tzinfo is None:
            raise InvalidError(error="starts_at must include timezone information")
        due_at = start.astimezone(UTC)
        timeline: list[dict[str, Any]] = []
        for step in steps:
            if step.step_type == SequenceStepType.DELAY.value:
                due_at += self._delay_delta(step.delay_value, step.delay_unit)
            template = await self._get_template_by_id(
                step.template_id, campaign.organization_id
            )
            timeline.append(
                {
                    "step_order": step.step_order,
                    "step_type": step.step_type,
                    "due_at": due_at,
                    "template_uuid": template["uuid"] if template else None,
                    "delay_value": step.delay_value,
                    "delay_unit": step.delay_unit,
                }
            )
        return {
            "starts_at": start.astimezone(UTC),
            "completes_at": due_at,
            "steps": timeline,
        }

    async def campaign_analytics(self, campaign: CampaignModel) -> dict[str, Any]:
        recipient = CampaignRecipientModel
        stmt = select(
            func.count(recipient.id).label("total_recipients"),
            func.count(recipient.id)
            .filter(recipient.status.in_(["pending", "queued", "sending"]))
            .label("pending"),
            func.count(recipient.id)
            .filter(recipient.sent_at.is_not(None))
            .label("sent"),
            func.count(recipient.id)
            .filter(recipient.delivered_at.is_not(None))
            .label("delivered"),
            func.count(recipient.id)
            .filter(recipient.opened_at.is_not(None))
            .label("opened"),
            func.count(recipient.id)
            .filter(recipient.clicked_at.is_not(None))
            .label("clicked"),
            func.count(recipient.id)
            .filter(recipient.replied_at.is_not(None))
            .label("replied"),
            func.count(recipient.id)
            .filter(recipient.bounced_at.is_not(None))
            .label("bounced"),
            func.count(recipient.id)
            .filter(recipient.status == RecipientStatus.FAILED.value)
            .label("failed"),
            func.count(recipient.id)
            .filter(recipient.unsubscribed_at.is_not(None))
            .label("unsubscribed"),
            func.count(recipient.id)
            .filter(
                recipient.status.in_(
                    [RecipientStatus.SKIPPED.value, RecipientStatus.STOPPED.value]
                )
            )
            .label("skipped"),
        ).where(
            recipient.campaign_id == campaign.id,
            recipient.organization_id == campaign.organization_id,
        )
        values = dict((await self.session.execute(stmt)).mappings().one())
        sent = int(values.get("sent") or 0)

        def rate(value: str) -> float:
            return round((int(values.get(value) or 0) / sent) * 100, 2) if sent else 0.0

        return {
            "campaign_uuid": campaign.uuid,
            **{key: int(value or 0) for key, value in values.items()},
            "delivery_rate": rate("delivered"),
            "open_rate": rate("opened"),
            "click_rate": rate("clicked"),
            "reply_rate": rate("replied"),
            "data_fresh_as_of": datetime.now(UTC),
        }

    async def _snapshot_recipients(self, campaign: CampaignModel) -> None:
        await self.repository.delete_recipients(campaign.id)
        contacts = await self._contact_rows(
            campaign.contact_list_id, campaign.organization_id
        )
        ab_test, variants = await self.repository.get_ab_test(campaign.id)
        _, sequence_steps = await self.repository.get_sequence(campaign.id)
        variant_dicts = [
            {
                "id": variant.id,
                "variant_type": variant.variant_type,
                "allocation_percentage": variant.allocation_percentage,
            }
            for variant in variants
        ]
        normalized_emails = [
            normalize_email(contact.get("email") or "") for contact in contacts
        ]
        suppressed = await self.repository.suppressed_emails(
            campaign.organization_id,
            [email for email in normalized_emails if email],
        )
        unique: dict[str, dict[str, Any]] = {}
        excluded = 0
        duplicates = 0
        for contact in contacts:
            normalized = normalize_email(contact.get("email") or "")
            reason = campaign_contact_ineligibility_reason(
                email=contact.get("email") or "",
                subscribed=bool(contact.get("subscribed")),
                status=contact.get("status"),
                verification_status=contact.get("verification_status"),
                archived_at=contact.get("archived_at"),
                suppressed=normalized in suppressed,
                bounce_risk=contact.get("bounce_risk"),
            )
            if reason:
                excluded += 1
                continue
            if normalized in unique:
                duplicates += 1
                continue
            unique[normalized] = contact

        now = datetime.now(UTC)
        recipients: list[CampaignRecipientModel] = []
        for normalized, contact in unique.items():
            variant_id = None
            ab_test_sampled = True
            recipient_status = RecipientStatus.PENDING.value
            next_attempt_at = now
            if campaign.campaign_type == CampaignType.AB_TEST.value:
                if not ab_test:
                    raise InvalidError(error="A/B test configuration is unavailable")
                if ab_test.winner_variant_id:
                    variant_id = ab_test.winner_variant_id
                    ab_test_sampled = False
                else:
                    ab_test_sampled = is_ab_test_sample_recipient(
                        normalized,
                        test_percentage=ab_test.test_percentage,
                        assignment_salt=campaign.uuid,
                    )
                    if ab_test_sampled:
                        variant_id = choose_ab_variant(
                            normalized,
                            variant_dicts,
                            assignment_salt=campaign.uuid,
                        )["id"]
                    else:
                        recipient_status = RecipientStatus.HOLDOUT.value
                        next_attempt_at = None
            personalization = dict(contact.get("metadata") or {})
            personalization.setdefault("email", contact["email"])
            recipients.append(
                CampaignRecipientModel(
                    organization_id=campaign.organization_id,
                    campaign_id=campaign.id,
                    contact_id=contact["id"],
                    ab_variant_id=variant_id,
                    email=contact["email"],
                    normalized_email=normalized,
                    personalization_data=personalization,
                    ab_test_sampled=ab_test_sampled,
                    status=recipient_status,
                    current_step_order=1,
                    next_attempt_at=next_attempt_at,
                )
            )
        await self.repository.add_recipients(recipients)
        variant_map = {variant.id: variant for variant in variants}
        for recipient in recipients:
            if campaign.campaign_type == CampaignType.SEQUENCE.value:
                for step in sequence_steps:
                    if step.step_type == SequenceStepType.EMAIL.value:
                        await self._logical_message(
                            campaign=campaign,
                            recipient=recipient,
                            step_order=step.step_order,
                            sequence_step=step,
                            variant=None,
                        )
            elif campaign.campaign_type == CampaignType.AB_TEST.value:
                # Snapshot both candidates before launch. This preserves content for
                # holdouts and for any unsent sample recipients released to the winner.
                for variant in variants:
                    await self._logical_message(
                        campaign=campaign,
                        recipient=recipient,
                        step_order=1,
                        sequence_step=None,
                        variant=variant,
                    )
            else:
                await self._logical_message(
                    campaign=campaign,
                    recipient=recipient,
                    step_order=1,
                    sequence_step=None,
                    variant=variant_map.get(recipient.ab_variant_id),
                )
        campaign.total_recipients = len(recipients)
        campaign.sent_count = 0
        campaign.failed_count = 0
        campaign.skipped_count = 0
        campaign.updated_at = now

    async def _process_single_recipient(
        self,
        *,
        campaign: CampaignModel,
        recipient: CampaignRecipientModel,
        account: dict[str, Any],
        actor_id: int,
        dry_run: bool,
        variant: CampaignABVariantModel | None,
    ) -> str:
        template_id = (
            variant.template_id
            if variant and variant.template_id
            else campaign.template_id
        )
        template = await self._get_template_by_id(template_id, campaign.organization_id)
        has_variant_override = bool(
            variant and variant.subject_override and variant.body_html_override
        )
        if not template and not has_variant_override:
            raise InvalidError(error="Campaign template is unavailable")
        subject = (
            variant.subject_override
            if variant and variant.subject_override
            else template["subject"]
        )
        body_html = (
            variant.body_html_override
            if variant and variant.body_html_override
            else template["body_html"]
        )
        message = None
        if not dry_run:
            message = await self._logical_message(
                campaign=campaign,
                recipient=recipient,
                step_order=1,
                sequence_step=None,
                variant=variant,
            )
            subject = message.subject_snapshot or subject
            body_html = message.body_html_snapshot or body_html
            if message.status == "sent":
                recipient.provider_message_id = message.provider_message_id
                recipient.status = RecipientStatus.SENT.value
                recipient.sent_at = recipient.sent_at or message.sent_at
                recipient.next_attempt_at = None
                return "sent"
            if message.status in {"sending", "uncertain"}:
                message.status = "uncertain"
                recipient.status = RecipientStatus.FAILED.value
                recipient.last_error_code = "SEND_OUTCOME_UNCERTAIN"
                recipient.last_error_message = (
                    "A previous send attempt has an uncertain provider outcome and "
                    "must be reconciled before retrying."
                )
                recipient.failed_at = datetime.now(UTC)
                recipient.next_attempt_at = None
                return "failed"

        await self._send(
            recipient=recipient,
            account=account,
            actor_id=actor_id,
            subject=subject,
            body_html=body_html,
            preheader=(
                message.preheader_snapshot
                if message and message.preheader_snapshot is not None
                else template.get("preheader")
                if template
                else None
            ),
            from_name=(
                message.from_name_snapshot
                if message and message.from_name_snapshot is not None
                else template.get("from_name")
                if template
                else None
            ),
            dry_run=dry_run,
            message=message,
        )
        if dry_run:
            return "sent"
        now = datetime.now(UTC)
        recipient.status = RecipientStatus.SENT.value
        recipient.sent_at = now
        recipient.next_attempt_at = None
        recipient.last_error_code = None
        recipient.last_error_message = None
        recipient.updated_at = now
        if variant and recipient.ab_test_sampled:
            variant.sent_count += 1
            variant.updated_at = now
        return "sent"

    async def _process_sequence_recipient(
        self,
        *,
        campaign: CampaignModel,
        recipient: CampaignRecipientModel,
        steps: dict[int, CampaignSequenceStepModel],
        account: dict[str, Any],
        actor_id: int,
        dry_run: bool,
    ) -> str:
        step = steps.get(recipient.current_step_order)
        if not step:
            if dry_run:
                return "sent"
            recipient.status = RecipientStatus.SENT.value
            recipient.sent_at = recipient.sent_at or datetime.now(UTC)
            recipient.next_attempt_at = None
            recipient.updated_at = datetime.now(UTC)
            return "sent"

        if step.step_type == SequenceStepType.DELAY.value:
            if dry_run:
                return "deferred"
            self._advance_sequence_after_step(
                recipient, steps, step.step_order, datetime.now(UTC)
            )
            return (
                "deferred" if recipient.status != RecipientStatus.SENT.value else "sent"
            )

        template = await self._get_template_by_id(
            step.template_id, campaign.organization_id
        )
        if not template and not (step.subject_override and step.body_html_override):
            raise InvalidError(
                error=f"Sequence step {step.step_order} has no email content"
            )
        subject = step.subject_override or template["subject"]
        body_html = step.body_html_override or template["body_html"]
        preheader = template.get("preheader") if template else None
        from_name = template.get("from_name") if template else None
        message = None
        if not dry_run:
            message = await self._logical_message(
                campaign=campaign,
                recipient=recipient,
                step_order=step.step_order,
                sequence_step=step,
                variant=None,
            )
            subject = message.subject_snapshot or subject
            body_html = message.body_html_snapshot or body_html
            preheader = (
                message.preheader_snapshot
                if message.preheader_snapshot is not None
                else preheader
            )
            from_name = (
                message.from_name_snapshot
                if message.from_name_snapshot is not None
                else from_name
            )
            if message.status == "sent":
                recipient.provider_message_id = message.provider_message_id
                recipient.sequence_step_id = step.id
                self._advance_sequence_after_step(
                    recipient, steps, step.step_order, datetime.now(UTC)
                )
                return "sent"
            if message.status in {"sending", "uncertain"}:
                message.status = "uncertain"
                recipient.status = RecipientStatus.FAILED.value
                recipient.last_error_code = "SEND_OUTCOME_UNCERTAIN"
                recipient.last_error_message = (
                    "A previous sequence-step send has an uncertain provider outcome."
                )
                recipient.failed_at = datetime.now(UTC)
                recipient.next_attempt_at = None
                return "failed"

        await self._send(
            recipient=recipient,
            account=account,
            actor_id=actor_id,
            subject=subject,
            body_html=body_html,
            preheader=preheader,
            from_name=from_name,
            dry_run=dry_run,
            message=message,
        )
        if dry_run:
            return "sent"
        recipient.sequence_step_id = step.id
        recipient.sent_at = datetime.now(UTC)
        recipient.attempt_count = 0
        recipient.last_error_code = None
        recipient.last_error_message = None
        self._advance_sequence_after_step(
            recipient, steps, step.step_order, datetime.now(UTC)
        )
        return "sent"

    def _advance_sequence_after_step(
        self,
        recipient: CampaignRecipientModel,
        steps: dict[int, CampaignSequenceStepModel],
        completed_order: int,
        now: datetime,
    ) -> None:
        next_order = completed_order + 1
        due_at = now
        while True:
            next_step = steps.get(next_order)
            if not next_step:
                recipient.current_step_order = next_order
                recipient.status = RecipientStatus.SENT.value
                recipient.next_attempt_at = None
                recipient.updated_at = now
                return
            if next_step.step_type != SequenceStepType.DELAY.value:
                recipient.current_step_order = next_order
                recipient.status = RecipientStatus.PENDING.value
                recipient.next_attempt_at = due_at
                recipient.updated_at = now
                return
            due_at += self._delay_delta(next_step.delay_value, next_step.delay_unit)
            next_order += 1

    async def _send(
        self,
        *,
        recipient: CampaignRecipientModel,
        account: dict[str, Any],
        actor_id: int,
        subject: str,
        body_html: str,
        preheader: str | None,
        from_name: str | None,
        dry_run: bool,
        message: CampaignMessageModel | None,
    ) -> None:
        variables = dict(recipient.personalization_data or {})
        if not variables.get("first_name") and variables.get("name"):
            variables["first_name"] = variables["name"]
        variables.setdefault("email", recipient.email)
        variables["unsubscribe_link"] = unsubscribe_url(
            organization_id=recipient.organization_id,
            email=recipient.email,
        )
        rendered = self.rendering_service.render_template(
            subject=subject,
            preheader=preheader,
            body_html=body_html,
            variables=variables,
        )
        if rendered.unresolved_variables:
            unresolved = ", ".join(rendered.unresolved_variables)
            raise InvalidError(error=f"Unresolved template variables: {unresolved}")
        body_text = self.rendering_service.html_to_plain_text(rendered.body_html)
        if dry_run:
            return

        if message is None:
            raise InvalidError(
                error="A durable campaign message is required for sending"
            )
        now = datetime.now(UTC)
        content_checksum = hashlib.sha256(
            f"{rendered.subject}\n{rendered.body_html}".encode()
        ).hexdigest()
        message.status = "sending"
        message.attempt_count += 1
        message.sending_started_at = now
        message.content_checksum = content_checksum
        message.last_error_code = None
        message.last_error_message = None
        message.updated_at = now
        recipient.status = RecipientStatus.SENDING.value
        recipient.queued_at = recipient.queued_at or now
        recipient.updated_at = now
        await self.session.flush()

        # Import the existing MailTracko sender lazily. Dry-run tests and API
        # imports therefore do not require provider credentials or worker wiring.
        from src.modules.email_template.email_template_container import (
            get_email_template_container,
        )
        from src.modules.email_template.infrastructure.email_sender.interface.test_email_sender_interface import (
            TestEmailMessage,
        )

        sender = get_email_template_container(self.session).test_email_sender()
        try:
            response = await sender.send(
                message=TestEmailMessage(
                    email_account_uuid=account["uuid"],
                    recipient_email=recipient.email,
                    subject=rendered.subject,
                    body_html=rendered.body_html,
                    body_text=body_text,
                    preheader=rendered.preheader,
                    from_name=from_name,
                ),
                organization_id=recipient.organization_id,
                actor_id=actor_id,
            )
        except Exception as exc:
            uncertain = is_uncertain_send_exception(exc)
            message.status = "uncertain" if uncertain else "failed"
            message.last_error_code = (
                "SEND_OUTCOME_UNCERTAIN" if uncertain else "SEND_FAILED"
            )
            message.last_error_message = str(exc)[:4000]
            message.failed_at = None if uncertain else datetime.now(UTC)
            message.updated_at = datetime.now(UTC)
            if uncertain:
                recipient.status = RecipientStatus.FAILED.value
                recipient.last_error_code = "SEND_OUTCOME_UNCERTAIN"
                recipient.last_error_message = "The provider outcome is uncertain. Reconcile this recipient before retrying."
                recipient.failed_at = message.updated_at
                recipient.next_attempt_at = None
                recipient.updated_at = message.updated_at
                raise UncertainSendOutcomeError(str(exc)) from exc
            raise
        provider_message_id = str(response.get("provider_message_id") or "") or None
        message.status = "sent"
        message.provider_message_id = provider_message_id
        message.provider_thread_id = (
            str(response.get("provider_thread_id") or "") or None
        )
        message.sent_at = datetime.now(UTC)
        message.updated_at = message.sent_at
        recipient.provider_message_id = provider_message_id
        recipient.provider_thread_id = message.provider_thread_id

    def _record_send_failure(
        self, recipient: CampaignRecipientModel, message: str
    ) -> str:
        now = datetime.now(UTC)
        recipient.last_error_code = "SEND_FAILED"
        recipient.last_error_message = message[:4000]
        recipient.updated_at = now
        if recipient.attempt_count < 3:
            recipient.status = RecipientStatus.PENDING.value
            recipient.next_attempt_at = now + timedelta(
                minutes=2 ** max(recipient.attempt_count, 1)
            )
            return "deferred"
        recipient.status = RecipientStatus.FAILED.value
        recipient.failed_at = now
        recipient.next_attempt_at = None
        return "failed"

    async def _refresh_counters(
        self, campaign: CampaignModel, *, actor_id: int | None = None
    ) -> None:
        stmt = (
            select(CampaignRecipientModel.status, func.count(CampaignRecipientModel.id))
            .where(CampaignRecipientModel.campaign_id == campaign.id)
            .group_by(CampaignRecipientModel.status)
        )
        rows = (await self.session.execute(stmt)).all()
        counts = {status: int(count) for status, count in rows}
        campaign.sent_count = sum(
            counts.get(status, 0)
            for status in (
                RecipientStatus.SENT.value,
                RecipientStatus.DELIVERED.value,
                RecipientStatus.OPENED.value,
                RecipientStatus.CLICKED.value,
                RecipientStatus.REPLIED.value,
            )
        )
        campaign.failed_count = counts.get(
            RecipientStatus.FAILED.value, 0
        ) + counts.get(RecipientStatus.BOUNCED.value, 0)
        persisted_skipped = sum(
            counts.get(status, 0)
            for status in (
                RecipientStatus.SKIPPED.value,
                RecipientStatus.UNSUBSCRIBED.value,
                RecipientStatus.STOPPED.value,
            )
        )
        campaign.skipped_count = max(campaign.skipped_count, persisted_skipped)
        campaign.updated_at = datetime.now(UTC)

        pending = sum(
            count
            for status, count in counts.items()
            if status not in _TERMINAL_RECIPIENT_STATUSES
        )
        if (
            campaign.total_recipients > 0
            and pending == 0
            and campaign.status == CampaignStatus.RUNNING.value
        ):
            await self._transition_campaign(
                campaign,
                CampaignStatus.COMPLETED.value,
                actor_id=actor_id,
                reason="All campaign recipients reached a terminal state",
            )
            sequence, _ = await self.repository.get_sequence(campaign.id)
            if sequence:
                sequence.status = SequenceStatus.COMPLETED.value
                sequence.updated_at = campaign.completed_at
            ab_test, ab_variants = await self.repository.get_ab_test(campaign.id)
            if ab_test and ab_test.status == ABTestStatus.RUNNING.value:
                if ab_test.auto_select_winner:
                    if not ab_test.winner_variant_id and self._ab_winner_ready(
                        ab_test, ab_variants
                    ):
                        await self.select_ab_winner(campaign=campaign)
                elif not ab_test.winner_variant_id:
                    ab_test.status = ABTestStatus.COMPLETED.value
                    ab_test.updated_at = campaign.completed_at
        await self.session.flush()

    async def _audience_preview(self, campaign: CampaignModel) -> dict[str, int]:
        contacts = await self._contact_rows(
            campaign.contact_list_id, campaign.organization_id
        )
        normalized_emails = [
            normalize_email(contact["email"] or "") for contact in contacts
        ]
        suppressed = await self.repository.suppressed_emails(
            campaign.organization_id,
            [email for email in normalized_emails if email],
        )
        ab_test = None
        if campaign.campaign_type == CampaignType.AB_TEST.value:
            ab_test, _ = await self.repository.get_ab_test(campaign.id)
        seen: set[str] = set()
        duplicates = 0
        excluded = 0
        eligible = 0
        ab_sampled = 0
        for contact in contacts:
            normalized = normalize_email(contact.get("email") or "")
            reason = campaign_contact_ineligibility_reason(
                email=contact.get("email") or "",
                subscribed=bool(contact.get("subscribed")),
                status=contact.get("status"),
                verification_status=contact.get("verification_status"),
                archived_at=contact.get("archived_at"),
                suppressed=normalized in suppressed,
                bounce_risk=contact.get("bounce_risk"),
            )
            if reason:
                excluded += 1
                continue
            if normalized in seen:
                duplicates += 1
                continue
            seen.add(normalized)
            eligible += 1
            if ab_test and is_ab_test_sample_recipient(
                normalized,
                test_percentage=ab_test.test_percentage,
                assignment_salt=campaign.uuid,
            ):
                ab_sampled += 1
        return {
            "total": len(contacts),
            "eligible": eligible,
            "excluded": excluded,
            "duplicates": duplicates,
            "ab_sampled": ab_sampled,
            "ab_holdout": max(eligible - ab_sampled, 0) if ab_test else 0,
        }

    async def _content_validation_errors(
        self,
        *,
        campaign: CampaignModel,
        steps: list[CampaignSequenceStepModel],
        variants: list[CampaignABVariantModel],
    ) -> list[str]:
        """Validate the same content/variables that the worker will render later."""
        content_items: list[tuple[str, str, str | None, str]] = []

        async def add_content(
            *,
            label: str,
            template_id: int | None,
            subject_override: str | None,
            body_override: str | None,
        ) -> None:
            template = await self._get_template_by_id(
                template_id, campaign.organization_id
            )
            if template and template.get("status") == "archived":
                content_items.append((label, "", None, ""))
                return
            subject = subject_override or (template or {}).get("subject")
            body_html = body_override or (template or {}).get("body_html")
            preheader = (template or {}).get("preheader")
            if subject and body_html:
                content_items.append((label, subject, preheader, body_html))

        if campaign.campaign_type == CampaignType.REGULAR.value:
            await add_content(
                label="Campaign template",
                template_id=campaign.template_id,
                subject_override=None,
                body_override=None,
            )
        elif campaign.campaign_type == CampaignType.SEQUENCE.value:
            for step in steps:
                if step.step_type == SequenceStepType.EMAIL.value:
                    await add_content(
                        label=f"Sequence step {step.step_order}",
                        template_id=step.template_id,
                        subject_override=step.subject_override,
                        body_override=step.body_html_override,
                    )
        elif campaign.campaign_type == CampaignType.AB_TEST.value:
            for variant in variants:
                await add_content(
                    label=f"A/B variant {variant.variant_type.upper()}",
                    template_id=variant.template_id,
                    subject_override=variant.subject_override,
                    body_override=variant.body_html_override,
                )

        errors: list[str] = []
        if any(
            not subject or not body_html for _, subject, _, body_html in content_items
        ):
            errors.append("One or more selected templates are archived")
            return errors

        contacts = await self._contact_rows(
            campaign.contact_list_id, campaign.organization_id
        )
        normalized_emails = [
            normalize_email(contact.get("email") or "") for contact in contacts
        ]
        suppressed = await self.repository.suppressed_emails(
            campaign.organization_id,
            [email for email in normalized_emails if email],
        )
        unresolved_by_content: dict[str, set[str]] = {}
        for contact in contacts:
            normalized = normalize_email(contact.get("email") or "")
            reason = campaign_contact_ineligibility_reason(
                email=contact.get("email") or "",
                subscribed=bool(contact.get("subscribed")),
                status=contact.get("status"),
                verification_status=contact.get("verification_status"),
                archived_at=contact.get("archived_at"),
                suppressed=normalized in suppressed,
                bounce_risk=contact.get("bounce_risk"),
            )
            if reason:
                continue
            variables = dict(contact.get("metadata") or {})
            if not variables.get("first_name") and variables.get("name"):
                variables["first_name"] = variables["name"]
            variables.setdefault("email", contact.get("email"))
            variables["unsubscribe_link"] = unsubscribe_url(
                organization_id=campaign.organization_id,
                email=contact.get("email"),
            )
            for label, subject, preheader, body_html in content_items:
                rendered = self.rendering_service.render_template(
                    subject=subject,
                    preheader=preheader,
                    body_html=body_html,
                    variables=variables,
                )
                if rendered.unresolved_variables:
                    unresolved_by_content.setdefault(label, set()).update(
                        rendered.unresolved_variables
                    )

        for label, variables in unresolved_by_content.items():
            errors.append(
                f"{label} has unresolved variables for one or more contacts: "
                + ", ".join(sorted(variables))
            )
        return errors

    async def _contact_rows(
        self, contact_list_id: int | None, organization_id: int
    ) -> list[dict[str, Any]]:
        if contact_list_id is None:
            return []
        result = await self.session.execute(
            text(
                "SELECT id, email, metadata, subscribed, status, verification_status, "
                "bounce_risk, last_bounced_at, archived_at FROM contact_contacts "
                "WHERE contact_list_id = :list_id AND organization_id = :organization_id"
            ),
            {"list_id": contact_list_id, "organization_id": organization_id},
        )
        return [dict(row) for row in result.mappings().all()]

    async def _resolve_email_account(
        self, account_uuid: str | None, organization_id: int
    ) -> dict[str, Any] | None:
        if account_uuid is None:
            return None
        result = await self.session.execute(
            text(
                "SELECT id, uuid, email, provider, status, health_status, sending_limit, "
                "daily_sent_count FROM email_accounts WHERE uuid = :uuid "
                "AND organization_id = :organization_id AND deleted_at IS NULL LIMIT 1"
            ),
            {"uuid": account_uuid, "organization_id": organization_id},
        )
        row = result.mappings().one_or_none()
        if not row:
            raise NotFoundError(error="Email account not found in this organization")
        return dict(row)

    async def _resolve_template(
        self, template_uuid: str | None, organization_id: int
    ) -> dict[str, Any] | None:
        if template_uuid is None:
            return None
        result = await self.session.execute(
            text(
                "SELECT id, uuid, name, subject, preheader, body_html, from_name, from_email, "
                "status, is_active, organization_id FROM templates WHERE uuid = :uuid "
                "AND deleted_at IS NULL AND is_active = true "
                "AND (organization_id = :organization_id OR organization_id IS NULL) LIMIT 1"
            ),
            {"uuid": template_uuid, "organization_id": organization_id},
        )
        row = result.mappings().one_or_none()
        if not row:
            raise NotFoundError(error="Template not found or unavailable")
        return dict(row)

    async def _resolve_contact_list(
        self, list_uuid: str | None, organization_id: int
    ) -> dict[str, Any] | None:
        if list_uuid is None:
            return None
        result = await self.session.execute(
            text(
                "SELECT id, uuid, name FROM contact_lists WHERE uuid = :uuid "
                "AND organization_id = :organization_id AND deleted_at IS NULL LIMIT 1"
            ),
            {"uuid": list_uuid, "organization_id": organization_id},
        )
        row = result.mappings().one_or_none()
        if not row:
            raise NotFoundError(error="Contact list not found in this organization")
        return dict(row)

    async def _get_email_account_by_id(
        self, account_id: int | None, organization_id: int
    ) -> dict[str, Any] | None:
        if account_id is None:
            return None
        result = await self.session.execute(
            text(
                "SELECT id, uuid, email, provider, status, health_status, sending_limit, "
                "daily_sent_count FROM email_accounts WHERE id = :id "
                "AND organization_id = :organization_id AND deleted_at IS NULL LIMIT 1"
            ),
            {"id": account_id, "organization_id": organization_id},
        )
        row = result.mappings().one_or_none()
        return dict(row) if row else None

    async def _get_template_by_id(
        self, template_id: int | None, organization_id: int
    ) -> dict[str, Any] | None:
        if template_id is None:
            return None
        result = await self.session.execute(
            text(
                "SELECT id, uuid, name, subject, preheader, body_html, from_name, from_email, "
                "status, is_active, organization_id FROM templates WHERE id = :id "
                "AND deleted_at IS NULL AND is_active = true "
                "AND (organization_id = :organization_id OR organization_id IS NULL) LIMIT 1"
            ),
            {"id": template_id, "organization_id": organization_id},
        )
        row = result.mappings().one_or_none()
        return dict(row) if row else None

    async def _get_contact_list_by_id(
        self, list_id: int | None, organization_id: int
    ) -> dict[str, Any] | None:
        if list_id is None:
            return None
        result = await self.session.execute(
            text(
                "SELECT id, uuid, name FROM contact_lists WHERE id = :id "
                "AND organization_id = :organization_id AND deleted_at IS NULL LIMIT 1"
            ),
            {"id": list_id, "organization_id": organization_id},
        )
        row = result.mappings().one_or_none()
        return dict(row) if row else None

    async def _logical_message(
        self,
        *,
        campaign: CampaignModel,
        recipient: CampaignRecipientModel,
        step_order: int,
        sequence_step: CampaignSequenceStepModel | None,
        variant: CampaignABVariantModel | None,
    ) -> CampaignMessageModel:
        variant_type = variant.variant_type if variant else None
        idempotency_key = build_message_idempotency_key(
            campaign_uuid=campaign.uuid,
            recipient_uuid=recipient.uuid,
            step_order=step_order,
            variant_type=variant_type,
        )
        message, _ = await self.repository.get_or_create_message(
            campaign=campaign,
            recipient=recipient,
            step_order=step_order,
            sequence_step_id=sequence_step.id if sequence_step else None,
            ab_variant_id=variant.id if variant else None,
            idempotency_key=idempotency_key,
        )
        if not message.subject_snapshot or not message.body_html_snapshot:
            await self._snapshot_message_content(
                message=message,
                campaign=campaign,
                sequence_step=sequence_step,
                variant=variant,
            )
        return message

    async def _snapshot_message_content(
        self,
        *,
        message: CampaignMessageModel,
        campaign: CampaignModel,
        sequence_step: CampaignSequenceStepModel | None,
        variant: CampaignABVariantModel | None,
    ) -> None:
        if sequence_step:
            template_id = sequence_step.template_id
            subject_override = sequence_step.subject_override
            body_override = sequence_step.body_html_override
        elif variant:
            template_id = variant.template_id or campaign.template_id
            subject_override = variant.subject_override
            body_override = variant.body_html_override
        else:
            template_id = campaign.template_id
            subject_override = None
            body_override = None

        template = await self._get_template_by_id(template_id, campaign.organization_id)
        subject = subject_override or (template or {}).get("subject")
        body_html = body_override or (template or {}).get("body_html")
        if not subject or not body_html:
            raise InvalidError(error="Campaign content is unavailable for snapshot")
        message.subject_snapshot = subject
        message.preheader_snapshot = (template or {}).get("preheader")
        message.body_html_snapshot = body_html
        message.from_name_snapshot = (template or {}).get("from_name")
        message.content_checksum = hashlib.sha256(
            f"{subject}\n{body_html}".encode()
        ).hexdigest()
        message.updated_at = datetime.now(UTC)

    async def _recipient_ineligibility_reason(
        self, recipient: CampaignRecipientModel
    ) -> str | None:
        if await self.repository.is_suppressed(
            recipient.organization_id, recipient.normalized_email
        ):
            return "suppressed"
        if recipient.contact_id is None:
            return None
        result = await self.session.execute(
            text(
                "SELECT email, subscribed, status, verification_status, bounce_risk, archived_at "
                "FROM contact_contacts WHERE id = :contact_id "
                "AND organization_id = :organization_id LIMIT 1"
            ),
            {
                "contact_id": recipient.contact_id,
                "organization_id": recipient.organization_id,
            },
        )
        contact = result.mappings().one_or_none()
        if contact is None:
            return "contact_unavailable"
        return campaign_contact_ineligibility_reason(
            email=contact.get("email") or recipient.email,
            subscribed=bool(contact.get("subscribed")),
            status=contact.get("status"),
            verification_status=contact.get("verification_status"),
            archived_at=contact.get("archived_at"),
            suppressed=False,
            bounce_risk=contact.get("bounce_risk"),
        )

    @staticmethod
    def _campaign_local_day_start(
        campaign: CampaignModel, moment_utc: datetime
    ) -> datetime:
        zone = ZoneInfo(campaign.timezone)
        local_moment = moment_utc.astimezone(zone)
        local_start = datetime.combine(local_moment.date(), time.min, tzinfo=zone)
        return local_start.astimezone(UTC)

    @staticmethod
    def _next_local_day_start(
        campaign: CampaignModel, moment_utc: datetime
    ) -> datetime:
        zone = ZoneInfo(campaign.timezone)
        local_moment = moment_utc.astimezone(zone)
        next_midnight = datetime.combine(
            local_moment.date() + timedelta(days=1), time.min, tzinfo=zone
        ).astimezone(UTC)
        return next_sending_window_at(
            next_midnight - timedelta(microseconds=1),
            timezone_name=campaign.timezone,
            start=campaign.sending_window_start,
            end=campaign.sending_window_end,
            days=campaign.sending_days,
        )

    async def _maybe_select_ab_winner(self, campaign: CampaignModel) -> None:
        if campaign.campaign_type != CampaignType.AB_TEST.value:
            return
        ab_test, variants = await self.repository.get_ab_test(campaign.id)
        if (
            not ab_test
            or not variants
            or not ab_test.auto_select_winner
            or ab_test.winner_variant_id
            or ab_test.status != ABTestStatus.RUNNING.value
        ):
            return
        if self._ab_winner_ready(ab_test, variants):
            await self.select_ab_winner(campaign=campaign)

    @staticmethod
    def _ab_winner_ready(
        ab_test: CampaignABTestModel, variants: list[CampaignABVariantModel]
    ) -> bool:
        sent_count = sum(int(variant.sent_count or 0) for variant in variants)
        return is_ab_winner_ready(
            sent_count=sent_count,
            minimum_sample_size=ab_test.minimum_sample_size,
            test_duration_hours=ab_test.test_duration_hours,
            started_at=ab_test.started_at,
        )

    @staticmethod
    def _delay_delta(delay_value: int | None, delay_unit: str | None) -> timedelta:
        value = delay_value or 0
        if delay_unit == DelayUnit.MINUTES.value:
            return timedelta(minutes=value)
        if delay_unit == DelayUnit.HOURS.value:
            return timedelta(hours=value)
        if delay_unit == DelayUnit.DAYS.value:
            return timedelta(days=value)
        if delay_unit == DelayUnit.WEEKS.value:
            return timedelta(weeks=value)
        raise InvalidError(error="Invalid sequence delay unit")

    async def _transition_campaign(
        self,
        campaign: CampaignModel,
        new_status: str,
        *,
        actor_id: int | None,
        reason: str | None = None,
    ) -> None:
        current_status = campaign.status
        if current_status == new_status:
            return
        if new_status not in _ALLOWED_STATUS_TRANSITIONS.get(current_status, set()):
            raise ConflictError(
                error=(
                    f"Campaign cannot transition from '{current_status}' "
                    f"to '{new_status}'"
                )
            )
        now = datetime.now(UTC)
        campaign.status = new_status
        campaign.updated_at = now
        if new_status == CampaignStatus.RUNNING.value:
            campaign.launched_at = campaign.launched_at or now
            campaign.paused_at = None
        elif new_status == CampaignStatus.PAUSED.value:
            campaign.paused_at = now
        elif new_status == CampaignStatus.COMPLETED.value:
            campaign.completed_at = now
        elif new_status == CampaignStatus.CANCELLED.value:
            campaign.cancelled_at = now
        elif new_status == CampaignStatus.ARCHIVED.value:
            campaign.archived_at = now
            # Archiving is reversible visibility/state management, not deletion.
            # Keep the row intact so archived campaigns remain auditable/listable.
            campaign.deleted_at = None
        await self.repository.add_state_history(
            campaign=campaign,
            from_status=current_status,
            to_status=new_status,
            actor_id=actor_id,
            reason=reason,
            transitioned_at=now,
        )

    @staticmethod
    def _ensure_editable(campaign: CampaignModel) -> None:
        if campaign.status not in _EDITABLE_STATUSES:
            raise ConflictError(
                error=f"Campaign cannot be edited while status is '{campaign.status}'"
            )

    @staticmethod
    def _reset_counters(campaign: CampaignModel) -> None:
        campaign.total_recipients = 0
        campaign.sent_count = 0
        campaign.failed_count = 0
        campaign.skipped_count = 0

    @staticmethod
    def _sequence_step_copy_dict(step: CampaignSequenceStepModel) -> dict[str, Any]:
        return {
            "step_order": step.step_order,
            "step_type": step.step_type,
            "template_id": step.template_id,
            "subject_override": step.subject_override,
            "body_html_override": step.body_html_override,
            "delay_value": step.delay_value,
            "delay_unit": step.delay_unit,
            "is_enabled": step.is_enabled,
        }

    @staticmethod
    def _ab_variant_copy_dict(variant: CampaignABVariantModel) -> dict[str, Any]:
        return {
            "variant_type": variant.variant_type,
            "name": variant.name,
            "template_id": variant.template_id,
            "subject_override": variant.subject_override,
            "body_html_override": variant.body_html_override,
            "allocation_percentage": variant.allocation_percentage,
        }

    @staticmethod
    def _recipient_to_dict(recipient: CampaignRecipientModel) -> dict[str, Any]:
        return {
            "uuid": recipient.uuid,
            "contact_id": recipient.contact_id,
            "email": recipient.email,
            "ab_test_sampled": recipient.ab_test_sampled,
            "status": recipient.status,
            "current_step_order": recipient.current_step_order,
            "attempt_count": recipient.attempt_count,
            "next_attempt_at": recipient.next_attempt_at,
            "provider_message_id": recipient.provider_message_id,
            "last_error_code": recipient.last_error_code,
            "last_error_message": recipient.last_error_message,
            "stop_reason": recipient.stop_reason,
            "stopped_at": recipient.stopped_at,
            "sent_at": recipient.sent_at,
            "delivered_at": recipient.delivered_at,
            "failed_at": recipient.failed_at,
            "bounced_at": recipient.bounced_at,
            "opened_at": recipient.opened_at,
            "clicked_at": recipient.clicked_at,
            "replied_at": recipient.replied_at,
            "unsubscribed_at": recipient.unsubscribed_at,
            "created_at": recipient.created_at,
        }
