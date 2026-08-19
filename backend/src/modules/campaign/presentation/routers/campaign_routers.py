from datetime import datetime
from types import SimpleNamespace
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from src.core.utils.response import CustomResponse as cr
from src.core.utils.response import CustomSuccessResponseSchema
from src.modules.campaign.application.services import CampaignService
from src.modules.campaign.domain.enums import CampaignStatus, CampaignType, RecipientStatus
from src.modules.campaign.infrastructure.uow import CampaignUOW
from src.modules.campaign.presentation.schemas.campaign_schemas import (
    ABTestResponseSchema,
    CampaignAnalyticsResponseSchema,
    CampaignDashboardSummarySchema,
    CampaignListResponseSchema,
    CampaignProcessResponseSchema,
    CampaignRecipientListResponseSchema,
    CampaignRecipientResponseSchema,
    CampaignResponseSchema,
    CampaignReviewResponseSchema,
    ConfigureABTestRequestSchema,
    ConfigureSequenceRequestSchema,
    CreateCampaignRequestSchema,
    ProcessCampaignRequestSchema,
    ReconcileSendOutcomeRequestSchema,
    RecipientEventRequestSchema,
    ScheduleCampaignRequestSchema,
    SelectABWinnerRequestSchema,
    SequencePreviewRequestSchema,
    SequencePreviewResponseSchema,
    SequenceResponseSchema,
    UpdateCampaignRequestSchema,
)
from src.shared.dependencies.access_guard import require_access
from src.shared.exceptions.base_exceptions import ForbiddenError, InvalidError, NotFoundError
from src.shared.infrastructure.db import get_async_session
from src.modules.platform.application.workspace_permissions import effective_workspace_permissions


router = APIRouter(
    dependencies=[Depends(require_access(authenticated=True, email_verified=True))]
)
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


async def _organization_context(request: Request, session: AsyncSession) -> int:
    result = await session.execute(
        text(
            "SELECT organization_id, role_code, permissions FROM org_organization_members "
            "WHERE user_id = :user_id AND status = 'active' AND deleted_at IS NULL LIMIT 1"
        ),
        {"user_id": request.state.user_id},
    )
    row = result.mappings().first()
    if not row:
        raise ForbiddenError(
            error="User does not belong to an active organization",
            errors={"code": "USER_HAS_NO_ORGANIZATION"},
        )
    member = SimpleNamespace(
        role_code=row["role_code"],
        permissions=row.get("permissions") or {},
    )
    permissions = effective_workspace_permissions(member)
    request.state.organization_id = row["organization_id"]
    request.state.organization_role_code = member.role_code
    request.state.organization_permissions = permissions
    if request.method not in {"GET", "HEAD", "OPTIONS"} and member.role_code != "owner":
        if not permissions.get("manage_campaigns", False):
            raise ForbiddenError(
                error="Your organization permissions do not allow managing campaigns",
                errors={"code": "CAMPAIGN_PERMISSION_REQUIRED"},
            )
    return int(row["organization_id"])


async def _campaign_or_404(
    service: CampaignService,
    campaign_uuid: str,
    organization_id: int,
    *,
    include_archived: bool = False,
):
    campaign = await service.repository.get_campaign(
        campaign_uuid,
        organization_id,
        include_archived=include_archived,
    )
    if not campaign:
        raise NotFoundError(error="Campaign not found")
    return campaign


@router.post("", response_model=CustomSuccessResponseSchema, status_code=HTTP_201_CREATED)
async def create_campaign(
    request: Request,
    body: CreateCampaignRequestSchema,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        data = await CampaignService(session).create_campaign(
            organization_id=organization_id,
            actor_id=request.state.user_id,
            payload=body,
        )
        payload = CampaignResponseSchema(**data).model_dump(mode="json")
    return cr.success(payload, "Campaign created successfully", HTTP_201_CREATED)


@router.get("/summary", response_model=CustomSuccessResponseSchema)
async def get_campaign_summary(request: Request, session: AsyncSessionDep):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        data = await CampaignService(session).repository.dashboard_summary(organization_id)
        payload = CampaignDashboardSummarySchema(**data).model_dump(mode="json")
    return cr.success(payload, "Campaign summary retrieved successfully")


@router.get("", response_model=CustomSuccessResponseSchema)
async def list_campaigns(
    request: Request,
    session: AsyncSessionDep,
    search: str | None = Query(default=None, max_length=150),
    status: CampaignStatus | None = None,
    campaign_type: CampaignType | None = None,
    email_account_uuid: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    include_archived: bool = False,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    async with CampaignUOW(session):
        if created_from and created_to and created_from > created_to:
            raise InvalidError(error="created_from cannot be later than created_to")
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        account_id = None
        if email_account_uuid:
            account = await service._resolve_email_account(email_account_uuid, organization_id)
            account_id = account["id"]
        items, total = await service.repository.list_campaigns(
            organization_id,
            limit=limit,
            offset=offset,
            search=search,
            status=status.value if status else None,
            campaign_type=campaign_type.value if campaign_type else None,
            email_account_id=account_id,
            created_from=created_from,
            created_to=created_to,
            include_archived=include_archived,
        )
        views = [CampaignResponseSchema(**(await service.campaign_view(item))) for item in items]
        payload = CampaignListResponseSchema(
            items=views,
            total=total,
            limit=limit,
            offset=offset,
        ).model_dump(mode="json")
    return cr.success(payload, "Campaigns retrieved successfully")


@router.get("/{campaign_uuid}", response_model=CustomSuccessResponseSchema)
async def get_campaign(
    campaign_uuid: str,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(
            service, campaign_uuid, organization_id, include_archived=True
        )
        payload = CampaignResponseSchema(
            **(await service.campaign_view(campaign))
        ).model_dump(mode="json")
    return cr.success(payload, "Campaign retrieved successfully")


@router.patch("/{campaign_uuid}", response_model=CustomSuccessResponseSchema)
async def update_campaign(
    campaign_uuid: str,
    body: UpdateCampaignRequestSchema,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        data = await service.update_campaign(
            campaign=campaign,
            organization_id=organization_id,
            actor_id=request.state.user_id,
            payload=body,
        )
        payload = CampaignResponseSchema(**data).model_dump(mode="json")
    return cr.success(payload, "Campaign updated successfully")


@router.post("/{campaign_uuid}/duplicate", response_model=CustomSuccessResponseSchema)
async def duplicate_campaign(
    campaign_uuid: str,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        data = await service.duplicate_campaign(
            campaign=campaign,
            actor_id=request.state.user_id,
        )
        payload = CampaignResponseSchema(**data).model_dump(mode="json")
    return cr.success(payload, "Campaign duplicated successfully", HTTP_201_CREATED)


@router.put("/{campaign_uuid}/sequence", response_model=CustomSuccessResponseSchema)
async def configure_sequence(
    campaign_uuid: str,
    body: ConfigureSequenceRequestSchema,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        data = await service.configure_sequence(
            campaign=campaign,
            organization_id=organization_id,
            actor_id=request.state.user_id,
            payload=body,
        )
        payload = SequenceResponseSchema(**data).model_dump(mode="json")
    return cr.success(payload, "Campaign sequence saved successfully")


@router.get("/{campaign_uuid}/sequence", response_model=CustomSuccessResponseSchema)
async def get_sequence(
    campaign_uuid: str,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        sequence, steps = await service.repository.get_sequence(campaign.id)
        if not sequence:
            raise NotFoundError(error="Campaign sequence not found")
        payload = SequenceResponseSchema(
            **(await service.sequence_view(sequence, steps))
        ).model_dump(mode="json")
    return cr.success(payload, "Campaign sequence retrieved successfully")

@router.post(
    "/{campaign_uuid}/sequence/preview",
    response_model=CustomSuccessResponseSchema,
)
async def preview_sequence(
    campaign_uuid: str,
    body: SequencePreviewRequestSchema,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        data = await service.sequence_preview(
            campaign=campaign, starts_at=body.starts_at
        )
        payload = SequencePreviewResponseSchema(**data).model_dump(mode="json")
    return cr.success(payload, "Campaign sequence preview generated successfully")


@router.put("/{campaign_uuid}/ab-test", response_model=CustomSuccessResponseSchema)
async def configure_ab_test(
    campaign_uuid: str,
    body: ConfigureABTestRequestSchema,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        data = await service.configure_ab_test(
            campaign=campaign,
            organization_id=organization_id,
            actor_id=request.state.user_id,
            payload=body,
        )
        payload = ABTestResponseSchema(**data).model_dump(mode="json")
    return cr.success(payload, "A/B test saved successfully")


@router.get("/{campaign_uuid}/ab-test", response_model=CustomSuccessResponseSchema)
async def get_ab_test(
    campaign_uuid: str,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        ab_test, variants = await service.repository.get_ab_test(campaign.id)
        if not ab_test:
            raise NotFoundError(error="A/B test configuration not found")
        payload = ABTestResponseSchema(
            **(await service.ab_test_view(ab_test, variants))
        ).model_dump(mode="json")
    return cr.success(payload, "A/B test retrieved successfully")


@router.post("/{campaign_uuid}/ab-test/winner", response_model=CustomSuccessResponseSchema)
async def select_ab_winner(
    campaign_uuid: str,
    body: SelectABWinnerRequestSchema,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        data = await service.select_ab_winner(
            campaign=campaign,
            variant_type=body.variant_type.value if body.variant_type else None,
        )
        payload = ABTestResponseSchema(**data).model_dump(mode="json")
    return cr.success(payload, "A/B test winner selected successfully")


@router.post("/{campaign_uuid}/review", response_model=CustomSuccessResponseSchema)
async def review_campaign(
    campaign_uuid: str,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        payload = CampaignReviewResponseSchema(
            **(
                await service.review_campaign(
                    campaign, actor_id=request.state.user_id
                )
            )
        ).model_dump(mode="json")
    return cr.success(payload, "Campaign review completed")


@router.post("/{campaign_uuid}/schedule", response_model=CustomSuccessResponseSchema)
async def schedule_campaign(
    campaign_uuid: str,
    body: ScheduleCampaignRequestSchema,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        data = await service.schedule_campaign(
            campaign=campaign,
            actor_id=request.state.user_id,
            scheduled_at=body.scheduled_at,
            timezone=body.timezone,
        )
        payload = CampaignResponseSchema(**data).model_dump(mode="json")
    return cr.success(payload, "Campaign scheduled successfully")


@router.post("/{campaign_uuid}/launch", response_model=CustomSuccessResponseSchema)
async def launch_campaign(
    campaign_uuid: str,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        data = await service.launch_campaign(
            campaign=campaign,
            actor_id=request.state.user_id,
        )
        payload = CampaignResponseSchema(**data).model_dump(mode="json")
    return cr.success(payload, "Campaign launched successfully")


@router.post("/{campaign_uuid}/process", response_model=CustomSuccessResponseSchema)
async def process_campaign(
    campaign_uuid: str,
    body: ProcessCampaignRequestSchema,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        data = await service.process_campaign(
            campaign=campaign,
            actor_id=request.state.user_id,
            dry_run=body.dry_run,
            limit=body.limit,
        )
        payload = CampaignProcessResponseSchema(**data).model_dump(mode="json")
    return cr.success(payload, "Campaign batch processed successfully")


@router.post("/{campaign_uuid}/pause", response_model=CustomSuccessResponseSchema)
async def pause_campaign(
    campaign_uuid: str,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        payload = CampaignResponseSchema(
            **(
                await service.pause_campaign(
                    campaign=campaign, actor_id=request.state.user_id
                )
            )
        ).model_dump(mode="json")
    return cr.success(payload, "Campaign paused successfully")


@router.post("/{campaign_uuid}/resume", response_model=CustomSuccessResponseSchema)
async def resume_campaign(
    campaign_uuid: str,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        payload = CampaignResponseSchema(
            **(
                await service.resume_campaign(
                    campaign=campaign, actor_id=request.state.user_id
                )
            )
        ).model_dump(mode="json")
    return cr.success(payload, "Campaign resumed successfully")


@router.post("/{campaign_uuid}/cancel", response_model=CustomSuccessResponseSchema)
async def cancel_campaign(
    campaign_uuid: str,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        payload = CampaignResponseSchema(
            **(
                await service.cancel_campaign(
                    campaign=campaign, actor_id=request.state.user_id
                )
            )
        ).model_dump(mode="json")
    return cr.success(payload, "Campaign cancelled successfully")


@router.post("/{campaign_uuid}/archive", response_model=CustomSuccessResponseSchema)
async def archive_campaign(
    campaign_uuid: str,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(
            service, campaign_uuid, organization_id, include_archived=True
        )
        payload = CampaignResponseSchema(
            **(
                await service.archive_campaign(
                    campaign=campaign, actor_id=request.state.user_id
                )
            )
        ).model_dump(mode="json")
    return cr.success(payload, "Campaign archived successfully")


@router.post("/{campaign_uuid}/restore", response_model=CustomSuccessResponseSchema)
async def restore_campaign(
    campaign_uuid: str,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(
            service, campaign_uuid, organization_id, include_archived=True
        )
        payload = CampaignResponseSchema(
            **(
                await service.restore_campaign(
                    campaign=campaign, actor_id=request.state.user_id
                )
            )
        ).model_dump(mode="json")
    return cr.success(payload, "Campaign restored successfully")


@router.delete("/{campaign_uuid}", response_model=CustomSuccessResponseSchema)
async def delete_campaign(
    campaign_uuid: str,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(
            service, campaign_uuid, organization_id, include_archived=True
        )
        payload = CampaignResponseSchema(
            **(
                await service.delete_campaign(
                    campaign=campaign, actor_id=request.state.user_id
                )
            )
        ).model_dump(mode="json")
    return cr.success(payload, "Campaign deleted successfully")


@router.get("/{campaign_uuid}/recipients", response_model=CustomSuccessResponseSchema)
async def list_campaign_recipients(
    campaign_uuid: str,
    request: Request,
    session: AsyncSessionDep,
    status: RecipientStatus | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        items, total = await service.repository.list_recipients(
            campaign.id,
            limit=limit,
            offset=offset,
            status=status.value if status else None,
        )
        payload = CampaignRecipientListResponseSchema(
            items=[
                CampaignRecipientResponseSchema(**service._recipient_to_dict(item))
                for item in items
            ],
            total=total,
            limit=limit,
            offset=offset,
        ).model_dump(mode="json")
    return cr.success(payload, "Campaign recipients retrieved successfully")

@router.get(
    "/{campaign_uuid}/analytics", response_model=CustomSuccessResponseSchema
)
async def get_campaign_analytics(
    campaign_uuid: str,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(
            service, campaign_uuid, organization_id, include_archived=True
        )
        payload = CampaignAnalyticsResponseSchema(
            **(await service.campaign_analytics(campaign))
        ).model_dump(mode="json")
    return cr.success(payload, "Campaign analytics retrieved successfully")


@router.post(
    "/{campaign_uuid}/recipients/{recipient_uuid}/events",
    response_model=CustomSuccessResponseSchema,
)
async def record_recipient_event(
    campaign_uuid: str,
    recipient_uuid: str,
    body: RecipientEventRequestSchema,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        data = await service.record_recipient_event(
            campaign=campaign,
            recipient_uuid=recipient_uuid,
            event_type=body.event_type,
            provider_event_id=body.provider_event_id,
            provider_message_id=body.provider_message_id,
            custom_event_name=body.custom_event_name,
            occurred_at=body.occurred_at,
            metadata=body.metadata,
            actor_id=request.state.user_id,
        )
        payload = CampaignRecipientResponseSchema(**data).model_dump(mode="json")
    return cr.success(payload, "Recipient event recorded successfully")


@router.post(
    "/{campaign_uuid}/recipients/{recipient_uuid}/reconcile-send",
    response_model=CustomSuccessResponseSchema,
)
async def reconcile_recipient_send(
    campaign_uuid: str,
    recipient_uuid: str,
    body: ReconcileSendOutcomeRequestSchema,
    request: Request,
    session: AsyncSessionDep,
):
    async with CampaignUOW(session):
        organization_id = await _organization_context(request, session)
        service = CampaignService(session)
        campaign = await _campaign_or_404(service, campaign_uuid, organization_id)
        data = await service.reconcile_send_outcome(
            campaign=campaign,
            recipient_uuid=recipient_uuid,
            outcome=body.outcome,
            provider_message_id=body.provider_message_id,
            provider_thread_id=body.provider_thread_id,
            actor_id=request.state.user_id,
        )
        payload = CampaignRecipientResponseSchema(**data).model_dump(mode="json")
    return cr.success(payload, "Recipient send outcome reconciled successfully")
