from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config.settings import config
from src.core.utils.response import CustomResponse as cr
from src.core.utils.response import CustomSuccessResponseSchema
from src.modules.auth.infrastructure.models.user_model import UserModel
from src.modules.auth.infrastructure.models.user_session_model import UserSessionModel
from src.modules.campaign.infrastructure.models.campaign_models import CampaignModel
from src.modules.organization.infrastructure.models.organization_model import (
    OrganizationModel,
)
from src.modules.platform.application.access import (
    require_platform_admin,
    write_audit_log,
)
from src.modules.platform.application.domain_health import check_domain_health
from src.modules.platform.application.stripe_client import StripeClient
from src.modules.platform.infrastructure.models.platform_models import (
    AbuseEventModel,
    BillingPlanModel,
    DomainHealthCheckModel,
    FeatureFlagModel,
    InvoiceModel,
    PaymentModel,
    PlatformSettingModel,
    PromotionModel,
    ProviderConfigModel,
    RefundModel,
    SubscriptionModel,
    SupportArticleModel,
    SupportTicketMessageModel,
    SupportTicketModel,
)
from src.modules.platform.presentation.schemas import (
    AbuseEventRequest,
    AdminStatusRequest,
    AdminUserStatusRequest,
    DomainHealthRequest,
    FeatureFlagRequest,
    MaintenanceRequest,
    PlanRequest,
    PromotionRequest,
    ProviderConfigRequest,
    RefundRequest,
    SupportArticleRequest,
    SupportTicketMessageRequest,
    SupportTicketUpdateRequest,
)
from src.shared.dependencies.access_guard import require_access
from src.shared.exceptions.base_exceptions import (
    ConflictError,
    InvalidError,
    NotFoundError,
)
from src.shared.infrastructure.db import get_async_session
from src.shared.infrastructure.encryption.fernet_encryption import encrypt

router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(require_access(authenticated=True, email_verified=True))],
)
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


def _require(request: Request) -> None:
    require_platform_admin(request)


def _plan_payload(plan: BillingPlanModel, include_provider_ids: bool = False) -> dict:
    payload = {
        "uuid": plan.uuid,
        "code": plan.code,
        "name": plan.name,
        "description": plan.description,
        "currency": plan.currency,
        "monthly_price_cents": plan.monthly_price_cents,
        "annual_price_cents": plan.annual_price_cents,
        "trial_days": plan.trial_days,
        "limits": plan.limits,
        "features": plan.features,
        "is_active": plan.is_active,
        "is_default": plan.is_default,
        "display_order": plan.display_order,
    }
    if include_provider_ids:
        payload["stripe_monthly_price_id"] = plan.stripe_monthly_price_id
        payload["stripe_annual_price_id"] = plan.stripe_annual_price_id
    return payload


def _ticket_payload(ticket: SupportTicketModel) -> dict:
    return {
        "uuid": ticket.uuid,
        "organization_id": ticket.organization_id,
        "subject": ticket.subject,
        "description": ticket.description,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "resolution": ticket.resolution,
        "resolved_at": ticket.resolved_at,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
    }


@router.get("/dashboard", response_model=CustomSuccessResponseSchema)
async def admin_dashboard(request: Request, session: AsyncSessionDep):
    _require(request)
    users = int((await session.execute(select(func.count(UserModel.id)))).scalar() or 0)
    active_users = int(
        (
            await session.execute(
                select(func.count(UserModel.id)).where(
                    UserModel.is_active.is_(True), UserModel.deleted_at.is_(None)
                )
            )
        ).scalar()
        or 0
    )
    organizations = int(
        (await session.execute(select(func.count(OrganizationModel.id)))).scalar() or 0
    )
    campaigns = int(
        (await session.execute(select(func.count(CampaignModel.id)))).scalar() or 0
    )
    tickets_open = int(
        (
            await session.execute(
                select(func.count(SupportTicketModel.id)).where(
                    SupportTicketModel.status.in_(
                        ("open", "in_progress", "waiting_customer")
                    )
                )
            )
        ).scalar()
        or 0
    )
    revenue_cents = int(
        (
            await session.execute(
                select(func.coalesce(func.sum(PaymentModel.amount_cents), 0)).where(
                    PaymentModel.status.in_(("succeeded", "paid"))
                )
            )
        ).scalar()
        or 0
    )
    refunds_cents = int(
        (
            await session.execute(
                select(func.coalesce(func.sum(RefundModel.amount_cents), 0)).where(
                    RefundModel.status.in_(("succeeded", "pending"))
                )
            )
        ).scalar()
        or 0
    )
    subscription_rows = (
        await session.execute(
            select(SubscriptionModel.status, func.count(SubscriptionModel.id)).group_by(
                SubscriptionModel.status
            )
        )
    ).all()
    abuse_open = int(
        (
            await session.execute(
                select(func.count(AbuseEventModel.id)).where(
                    AbuseEventModel.status == "open"
                )
            )
        ).scalar()
        or 0
    )
    redis_healthy = False
    redis_client = Redis.from_url(
        config.REDIS_URL,
        socket_connect_timeout=1,
        socket_timeout=1,
    )
    try:
        redis_healthy = bool(await redis_client.ping())
    except (RedisConnectionError, RedisTimeoutError):
        redis_healthy = False
    finally:
        await redis_client.aclose()
    return cr.success(
        data={
            "users": {"total": users, "active": active_users},
            "organizations": organizations,
            "campaigns": campaigns,
            "support": {"open_tickets": tickets_open},
            "billing": {
                "gross_revenue_cents": revenue_cents,
                "refunds_cents": refunds_cents,
                "net_revenue_cents": revenue_cents - refunds_cents,
                "subscriptions": {
                    status: int(count) for status, count in subscription_rows
                },
            },
            "risk": {"open_abuse_events": abuse_open},
            "infrastructure": {
                "database": "healthy",
                "redis": "healthy" if redis_healthy else "unavailable",
            },
        },
        message="Platform dashboard retrieved",
    )


@router.get("/users", response_model=CustomSuccessResponseSchema)
async def list_users(
    request: Request,
    session: AsyncSessionDep,
    search: str | None = Query(default=None, max_length=200),
    active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    _require(request)
    filters = []
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(UserModel.email.ilike(pattern), UserModel.full_name.ilike(pattern))
        )
    if active is not None:
        filters.append(UserModel.is_active.is_(active))
    total = int(
        (
            await session.execute(select(func.count(UserModel.id)).where(*filters))
        ).scalar()
        or 0
    )
    users = (
        (
            await session.execute(
                select(UserModel)
                .where(*filters)
                .order_by(UserModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return cr.success(
        data={
            "items": [
                {
                    "uuid": user.uuid,
                    "full_name": user.full_name,
                    "email": user.email,
                    "is_active": user.is_active,
                    "email_verified_at": user.email_verified_at,
                    "last_login_at": user.last_login_at,
                    "scheduled_deletion_at": user.scheduled_deletion_at,
                    "created_at": user.created_at,
                }
                for user in users
            ],
            "total": total,
        },
        message="Users retrieved",
    )


@router.patch("/users/{user_uuid}/status", response_model=CustomSuccessResponseSchema)
async def update_user_status(
    request: Request,
    user_uuid: str,
    body: AdminUserStatusRequest,
    session: AsyncSessionDep,
):
    _require(request)
    user = (
        (await session.execute(select(UserModel).where(UserModel.uuid == user_uuid)))
        .scalars()
        .first()
    )
    if not user:
        raise NotFoundError(error="User not found")
    if user.id == request.state.user_id and not body.is_active:
        raise InvalidError(error="You cannot suspend your own administrator account")
    user.is_active = body.is_active
    now = datetime.now(UTC)
    user.updated_at = now
    if not body.is_active:
        # Suspension must invalidate already-issued sessions immediately.
        await session.execute(
            update(UserSessionModel)
            .where(
                UserSessionModel.user_id == user.id,
                UserSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=now, updated_at=now)
        )
    await write_audit_log(
        session,
        request,
        action="admin.user_status_changed",
        resource_type="user",
        resource_uuid=user.uuid,
        metadata={"is_active": body.is_active},
    )
    await session.commit()
    return cr.success(
        data={"uuid": user.uuid, "is_active": user.is_active}, message="User updated"
    )


@router.delete("/users/{user_uuid}", response_model=CustomSuccessResponseSchema)
async def delete_user(
    request: Request,
    user_uuid: str,
    session: AsyncSessionDep,
):
    _require(request)
    user = (
        (await session.execute(select(UserModel).where(UserModel.uuid == user_uuid)))
        .scalars()
        .first()
    )
    if not user:
        raise NotFoundError(error="User not found")
    if user.id == request.state.user_id:
        raise InvalidError(error="You cannot delete your own administrator account")
    now = datetime.now(UTC)
    user.is_active = False
    user.deleted_at = now
    user.scheduled_deletion_at = now
    user.updated_at = now
    await session.execute(
        update(UserSessionModel)
        .where(
            UserSessionModel.user_id == user.id, UserSessionModel.revoked_at.is_(None)
        )
        .values(revoked_at=now, updated_at=now)
    )
    await write_audit_log(
        session,
        request,
        action="admin.user_deleted",
        resource_type="user",
        resource_uuid=user.uuid,
    )
    await session.commit()
    return cr.success(data={"uuid": user.uuid, "deleted": True}, message="User deleted")


@router.get("/organizations", response_model=CustomSuccessResponseSchema)
async def list_organizations(
    request: Request,
    session: AsyncSessionDep,
    search: str | None = Query(default=None, max_length=200),
    status: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    _require(request)
    filters = [OrganizationModel.deleted_at.is_(None)]
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                OrganizationModel.name.ilike(pattern),
                OrganizationModel.domain_email.ilike(pattern),
            )
        )
    if status:
        filters.append(OrganizationModel.status == status)
    total = int(
        (
            await session.execute(
                select(func.count(OrganizationModel.id)).where(*filters)
            )
        ).scalar()
        or 0
    )
    rows = (
        await session.execute(
            select(
                OrganizationModel,
                UserModel.email,
                SubscriptionModel.status,
                BillingPlanModel.name,
            )
            .join(UserModel, UserModel.id == OrganizationModel.owner_id)
            .outerjoin(
                SubscriptionModel,
                SubscriptionModel.organization_id == OrganizationModel.id,
            )
            .outerjoin(
                BillingPlanModel, BillingPlanModel.id == SubscriptionModel.plan_id
            )
            .where(*filters)
            .order_by(OrganizationModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return cr.success(
        data={
            "items": [
                {
                    "uuid": org.uuid,
                    "name": org.name,
                    "domain_email": org.domain_email,
                    "status": org.status,
                    "owner_email": owner_email,
                    "subscription_status": subscription_status,
                    "plan_name": plan_name,
                    "created_at": org.created_at,
                }
                for org, owner_email, subscription_status, plan_name in rows
            ],
            "total": total,
        },
        message="Organizations retrieved",
    )


@router.patch(
    "/organizations/{organization_uuid}/status",
    response_model=CustomSuccessResponseSchema,
)
async def update_organization_status(
    request: Request,
    organization_uuid: str,
    body: AdminStatusRequest,
    session: AsyncSessionDep,
):
    _require(request)
    organization = (
        (
            await session.execute(
                select(OrganizationModel).where(
                    OrganizationModel.uuid == organization_uuid
                )
            )
        )
        .scalars()
        .first()
    )
    if not organization:
        raise NotFoundError(error="Organization not found")
    organization.status = body.status
    organization.updated_at = datetime.now(UTC)
    await write_audit_log(
        session,
        request,
        action="admin.organization_status_changed",
        resource_type="organization",
        resource_uuid=organization.uuid,
        metadata={"status": body.status},
        organization_id=organization.id,
    )
    await session.commit()
    return cr.success(
        data={"uuid": organization.uuid, "status": organization.status},
        message="Organization updated",
    )


@router.delete(
    "/organizations/{organization_uuid}", response_model=CustomSuccessResponseSchema
)
async def delete_organization(
    request: Request,
    organization_uuid: str,
    session: AsyncSessionDep,
):
    _require(request)
    organization = (
        (
            await session.execute(
                select(OrganizationModel).where(
                    OrganizationModel.uuid == organization_uuid,
                    OrganizationModel.deleted_at.is_(None),
                )
            )
        )
        .scalars()
        .first()
    )
    if not organization:
        raise NotFoundError(error="Organization not found")
    now = datetime.now(UTC)
    organization.status = "deleted"
    organization.deleted_at = now
    organization.deletion_requested_at = now
    organization.deletion_requested_by_id = request.state.user_id
    organization.scheduled_deletion_at = now
    organization.updated_at = now
    await write_audit_log(
        session,
        request,
        action="admin.organization_deleted",
        resource_type="organization",
        resource_uuid=organization.uuid,
        organization_id=organization.id,
    )
    await session.commit()
    return cr.success(
        data={"uuid": organization.uuid, "deleted": True},
        message="Organization deleted",
    )


@router.get("/billing/configuration", response_model=CustomSuccessResponseSchema)
async def billing_configuration(request: Request):
    """Return Stripe readiness without exposing any provider credentials."""

    _require(request)
    mode = "unconfigured"
    if config.STRIPE_SECRET_KEY.startswith("sk_test_"):
        mode = "test"
    elif config.STRIPE_SECRET_KEY.startswith("sk_live_"):
        mode = "live"
    elif config.STRIPE_SECRET_KEY:
        mode = "configured"
    return cr.success(
        data={
            "billing_enabled": config.BILLING_ENABLED,
            "mode": mode,
            "secret_key_configured": bool(config.STRIPE_SECRET_KEY),
            "publishable_key_configured": bool(config.STRIPE_PUBLISHABLE_KEY),
            "webhook_secret_configured": bool(config.STRIPE_WEBHOOK_SECRET),
            "api_version": config.STRIPE_API_VERSION or "Stripe account default",
            "automatic_tax": config.STRIPE_AUTOMATIC_TAX,
            "collect_billing_address": config.STRIPE_COLLECT_BILLING_ADDRESS,
            "proration_behavior": config.STRIPE_PRORATION_BEHAVIOR,
            "webhook_path": "/api/v1/billing/webhooks/stripe",
        },
        message="Billing configuration retrieved",
    )


@router.get("/plans", response_model=CustomSuccessResponseSchema)
async def admin_list_plans(request: Request, session: AsyncSessionDep):
    _require(request)
    plans = (
        (
            await session.execute(
                select(BillingPlanModel).order_by(
                    BillingPlanModel.display_order.asc(),
                    BillingPlanModel.created_at.asc(),
                )
            )
        )
        .scalars()
        .all()
    )
    return cr.success(
        data={
            "items": [_plan_payload(plan, include_provider_ids=True) for plan in plans]
        },
        message="Plans retrieved",
    )


@router.post("/plans", response_model=CustomSuccessResponseSchema)
async def create_plan(request: Request, body: PlanRequest, session: AsyncSessionDep):
    _require(request)
    existing = (
        (
            await session.execute(
                select(BillingPlanModel).where(BillingPlanModel.code == body.code)
            )
        )
        .scalars()
        .first()
    )
    if existing:
        raise ConflictError(error="A billing plan with this code already exists")
    if body.is_default:
        for plan in (await session.execute(select(BillingPlanModel))).scalars().all():
            plan.is_default = False
    plan = BillingPlanModel(**body.model_dump())
    session.add(plan)
    await session.flush()
    await write_audit_log(
        session,
        request,
        action="admin.plan_created",
        resource_type="billing_plan",
        resource_uuid=plan.uuid,
        metadata={"code": plan.code},
    )
    await session.commit()
    return cr.success(
        data=_plan_payload(plan, include_provider_ids=True),
        message="Plan created",
        status_code=201,
    )


@router.put("/plans/{plan_uuid}", response_model=CustomSuccessResponseSchema)
async def update_plan(
    request: Request,
    plan_uuid: str,
    body: PlanRequest,
    session: AsyncSessionDep,
):
    _require(request)
    plan = (
        (
            await session.execute(
                select(BillingPlanModel).where(BillingPlanModel.uuid == plan_uuid)
            )
        )
        .scalars()
        .first()
    )
    if not plan:
        raise NotFoundError(error="Billing plan not found")
    duplicate = (
        (
            await session.execute(
                select(BillingPlanModel).where(
                    BillingPlanModel.code == body.code, BillingPlanModel.id != plan.id
                )
            )
        )
        .scalars()
        .first()
    )
    if duplicate:
        raise ConflictError(error="A billing plan with this code already exists")
    if body.is_default:
        for other in (await session.execute(select(BillingPlanModel))).scalars().all():
            other.is_default = other.id == plan.id
    for key, value in body.model_dump().items():
        setattr(plan, key, value)
    plan.updated_at = datetime.now(UTC)
    await write_audit_log(
        session,
        request,
        action="admin.plan_updated",
        resource_type="billing_plan",
        resource_uuid=plan.uuid,
    )
    await session.commit()
    return cr.success(
        data=_plan_payload(plan, include_provider_ids=True), message="Plan updated"
    )


@router.get("/promotions", response_model=CustomSuccessResponseSchema)
async def list_promotions(request: Request, session: AsyncSessionDep):
    _require(request)
    promotions = (
        (
            await session.execute(
                select(PromotionModel).order_by(PromotionModel.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return cr.success(
        data={
            "items": [
                {
                    "uuid": item.uuid,
                    "code": item.code,
                    "name": item.name,
                    "percent_off": item.percent_off,
                    "amount_off_cents": item.amount_off_cents,
                    "currency": item.currency,
                    "max_redemptions": item.max_redemptions,
                    "redemption_count": item.redemption_count,
                    "starts_at": item.starts_at,
                    "ends_at": item.ends_at,
                    "is_active": item.is_active,
                }
                for item in promotions
            ]
        },
        message="Promotions retrieved",
    )


@router.post("/promotions", response_model=CustomSuccessResponseSchema)
async def create_promotion(
    request: Request, body: PromotionRequest, session: AsyncSessionDep
):
    _require(request)
    code = body.code.strip().upper()
    existing = (
        (
            await session.execute(
                select(PromotionModel).where(PromotionModel.code == code)
            )
        )
        .scalars()
        .first()
    )
    if existing:
        raise ConflictError(error="A promotion with this code already exists")
    values = body.model_dump()
    values["code"] = code
    promotion = PromotionModel(**values)
    session.add(promotion)
    await session.flush()
    await write_audit_log(
        session,
        request,
        action="admin.promotion_created",
        resource_type="promotion",
        resource_uuid=promotion.uuid,
        metadata={"code": code},
    )
    await session.commit()
    return cr.success(
        data={"uuid": promotion.uuid, "code": promotion.code},
        message="Promotion created",
        status_code=201,
    )


@router.get("/payments", response_model=CustomSuccessResponseSchema)
async def list_payments(
    request: Request,
    session: AsyncSessionDep,
    status: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    _require(request)
    filters = []
    if status:
        filters.append(PaymentModel.status == status)
    total = int(
        (
            await session.execute(select(func.count(PaymentModel.id)).where(*filters))
        ).scalar()
        or 0
    )
    rows = (
        await session.execute(
            select(PaymentModel, OrganizationModel.name, InvoiceModel.number)
            .join(
                OrganizationModel, OrganizationModel.id == PaymentModel.organization_id
            )
            .outerjoin(InvoiceModel, InvoiceModel.id == PaymentModel.invoice_id)
            .where(*filters)
            .order_by(PaymentModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return cr.success(
        data={
            "items": [
                {
                    "uuid": payment.uuid,
                    "organization_name": organization_name,
                    "invoice_number": invoice_number,
                    "provider_payment_intent_id": payment.provider_payment_intent_id,
                    "amount_cents": payment.amount_cents,
                    "refunded_cents": payment.refunded_cents,
                    "currency": payment.currency,
                    "status": payment.status,
                    "failure_message": payment.failure_message,
                    "created_at": payment.created_at,
                }
                for payment, organization_name, invoice_number in rows
            ],
            "total": total,
        },
        message="Payments retrieved",
    )


@router.post(
    "/payments/{payment_uuid}/refund", response_model=CustomSuccessResponseSchema
)
async def refund_payment(
    request: Request,
    payment_uuid: str,
    body: RefundRequest,
    session: AsyncSessionDep,
):
    _require(request)
    payment = (
        (
            await session.execute(
                select(PaymentModel).where(PaymentModel.uuid == payment_uuid)
            )
        )
        .scalars()
        .first()
    )
    if not payment:
        raise NotFoundError(error="Payment not found")
    refundable = payment.amount_cents - payment.refunded_cents
    amount = body.amount_cents or refundable
    if amount <= 0 or amount > refundable:
        raise InvalidError(
            error="Refund amount exceeds the remaining refundable amount"
        )
    result = await StripeClient().create_refund(
        payment_intent_id=payment.provider_payment_intent_id,
        amount_cents=amount,
        reason=body.reason,
    )
    refund = RefundModel(
        organization_id=payment.organization_id,
        payment_id=payment.id,
        provider_refund_id=result["id"],
        amount_cents=int(result.get("amount") or amount),
        status=result.get("status") or "pending",
        reason=body.reason,
        requested_by_id=request.state.user_id,
    )
    session.add(refund)
    payment.refunded_cents += refund.amount_cents
    await session.flush()
    await write_audit_log(
        session,
        request,
        action="admin.payment_refunded",
        resource_type="payment",
        resource_uuid=payment.uuid,
        metadata={"refund_uuid": refund.uuid, "amount_cents": refund.amount_cents},
        organization_id=payment.organization_id,
    )
    await session.commit()
    return cr.success(
        data={
            "uuid": refund.uuid,
            "amount_cents": refund.amount_cents,
            "status": refund.status,
        },
        message="Refund submitted",
        status_code=201,
    )


@router.get("/support/tickets", response_model=CustomSuccessResponseSchema)
async def admin_list_tickets(
    request: Request,
    session: AsyncSessionDep,
    status: str | None = Query(default=None, max_length=30),
    priority: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    _require(request)
    filters = []
    if status:
        filters.append(SupportTicketModel.status == status)
    if priority:
        filters.append(SupportTicketModel.priority == priority)
    total = int(
        (
            await session.execute(
                select(func.count(SupportTicketModel.id)).where(*filters)
            )
        ).scalar()
        or 0
    )
    rows = (
        await session.execute(
            select(SupportTicketModel, OrganizationModel.name, UserModel.email)
            .join(
                OrganizationModel,
                OrganizationModel.id == SupportTicketModel.organization_id,
            )
            .join(UserModel, UserModel.id == SupportTicketModel.created_by_id)
            .where(*filters)
            .order_by(SupportTicketModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return cr.success(
        data={
            "items": [
                {
                    **_ticket_payload(ticket),
                    "organization_name": org_name,
                    "requester_email": email,
                }
                for ticket, org_name, email in rows
            ],
            "total": total,
        },
        message="Support queue retrieved",
    )


@router.patch(
    "/support/tickets/{ticket_uuid}", response_model=CustomSuccessResponseSchema
)
async def admin_update_ticket(
    request: Request,
    ticket_uuid: str,
    body: SupportTicketUpdateRequest,
    session: AsyncSessionDep,
):
    _require(request)
    ticket = (
        (
            await session.execute(
                select(SupportTicketModel).where(SupportTicketModel.uuid == ticket_uuid)
            )
        )
        .scalars()
        .first()
    )
    if not ticket:
        raise NotFoundError(error="Support ticket not found")
    values = body.model_dump(exclude_unset=True)
    assignee_uuid = values.pop("assignee_user_uuid", None)
    if assignee_uuid:
        assignee = (
            (
                await session.execute(
                    select(UserModel).where(UserModel.uuid == assignee_uuid)
                )
            )
            .scalars()
            .first()
        )
        if not assignee:
            raise NotFoundError(error="Assignee not found")
        ticket.assignee_user_id = assignee.id
    for key, value in values.items():
        setattr(ticket, key, value)
    if ticket.status in {"resolved", "closed"}:
        ticket.resolved_at = ticket.resolved_at or datetime.now(UTC)
    else:
        ticket.resolved_at = None
    ticket.updated_at = datetime.now(UTC)
    await write_audit_log(
        session,
        request,
        action="admin.support_ticket_updated",
        resource_type="support_ticket",
        resource_uuid=ticket.uuid,
        metadata={"fields": sorted(body.model_fields_set)},
        organization_id=ticket.organization_id,
    )
    await session.commit()
    return cr.success(data=_ticket_payload(ticket), message="Support ticket updated")


@router.post(
    "/support/tickets/{ticket_uuid}/messages",
    response_model=CustomSuccessResponseSchema,
)
async def admin_add_ticket_message(
    request: Request,
    ticket_uuid: str,
    body: SupportTicketMessageRequest,
    session: AsyncSessionDep,
):
    _require(request)
    ticket = (
        (
            await session.execute(
                select(SupportTicketModel).where(SupportTicketModel.uuid == ticket_uuid)
            )
        )
        .scalars()
        .first()
    )
    if not ticket:
        raise NotFoundError(error="Support ticket not found")
    message = SupportTicketMessageModel(
        ticket_id=ticket.id,
        author_user_id=request.state.user_id,
        body=body.body.strip(),
        attachments=body.attachments,
        is_internal=body.is_internal,
    )
    session.add(message)
    if not body.is_internal:
        ticket.status = "waiting_customer"
    ticket.updated_at = datetime.now(UTC)
    await session.flush()
    await session.commit()
    return cr.success(
        data={"uuid": message.uuid, "created_at": message.created_at},
        message="Support message added",
        status_code=201,
    )


@router.get("/support/articles", response_model=CustomSuccessResponseSchema)
async def admin_list_articles(request: Request, session: AsyncSessionDep):
    _require(request)
    articles = (
        (
            await session.execute(
                select(SupportArticleModel).order_by(
                    SupportArticleModel.display_order.asc(),
                    SupportArticleModel.title.asc(),
                )
            )
        )
        .scalars()
        .all()
    )
    return cr.success(
        data={
            "items": [
                {
                    "uuid": item.uuid,
                    "slug": item.slug,
                    "title": item.title,
                    "category": item.category,
                    "summary": item.summary,
                    "content": item.content,
                    "tags": item.tags,
                    "is_published": item.is_published,
                    "display_order": item.display_order,
                    "updated_at": item.updated_at,
                }
                for item in articles
            ]
        },
        message="Support articles retrieved",
    )


@router.post("/support/articles", response_model=CustomSuccessResponseSchema)
async def create_article(
    request: Request,
    body: SupportArticleRequest,
    session: AsyncSessionDep,
):
    _require(request)
    existing = (
        (
            await session.execute(
                select(SupportArticleModel).where(SupportArticleModel.slug == body.slug)
            )
        )
        .scalars()
        .first()
    )
    if existing:
        raise ConflictError(error="A support article with this slug already exists")
    article = SupportArticleModel(**body.model_dump())
    session.add(article)
    await session.flush()
    await write_audit_log(
        session,
        request,
        action="admin.support_article_created",
        resource_type="support_article",
        resource_uuid=article.uuid,
        metadata={"slug": article.slug},
    )
    await session.commit()
    return cr.success(
        data={"uuid": article.uuid}, message="Article created", status_code=201
    )


@router.put(
    "/support/articles/{article_uuid}", response_model=CustomSuccessResponseSchema
)
async def update_article(
    request: Request,
    article_uuid: str,
    body: SupportArticleRequest,
    session: AsyncSessionDep,
):
    _require(request)
    article = (
        (
            await session.execute(
                select(SupportArticleModel).where(
                    SupportArticleModel.uuid == article_uuid
                )
            )
        )
        .scalars()
        .first()
    )
    if not article:
        raise NotFoundError(error="Support article not found")
    duplicate = (
        (
            await session.execute(
                select(SupportArticleModel).where(
                    SupportArticleModel.slug == body.slug,
                    SupportArticleModel.id != article.id,
                )
            )
        )
        .scalars()
        .first()
    )
    if duplicate:
        raise ConflictError(error="A support article with this slug already exists")
    for key, value in body.model_dump().items():
        setattr(article, key, value)
    article.updated_at = datetime.now(UTC)
    await session.commit()
    return cr.success(data={"uuid": article.uuid}, message="Article updated")


@router.get("/provider-configs", response_model=CustomSuccessResponseSchema)
async def list_provider_configs(request: Request, session: AsyncSessionDep):
    _require(request)
    items = (
        (
            await session.execute(
                select(ProviderConfigModel).order_by(
                    ProviderConfigModel.provider.asc(),
                    ProviderConfigModel.config_key.asc(),
                )
            )
        )
        .scalars()
        .all()
    )
    return cr.success(
        data={
            "items": [
                {
                    "uuid": item.uuid,
                    "provider": item.provider,
                    "config_key": item.config_key,
                    "value": "••••••••" if item.is_secret else "Configured",
                    "is_secret": item.is_secret,
                    "is_active": item.is_active,
                    "updated_at": item.updated_at,
                }
                for item in items
            ]
        },
        message="Provider configurations retrieved",
    )


@router.put("/provider-configs", response_model=CustomSuccessResponseSchema)
async def upsert_provider_config(
    request: Request,
    body: ProviderConfigRequest,
    session: AsyncSessionDep,
):
    _require(request)
    provider = body.provider.strip().lower()
    key = body.config_key.strip().lower()
    item = (
        (
            await session.execute(
                select(ProviderConfigModel).where(
                    ProviderConfigModel.provider == provider,
                    ProviderConfigModel.config_key == key,
                )
            )
        )
        .scalars()
        .first()
    )
    if not item:
        item = ProviderConfigModel(
            provider=provider,
            config_key=key,
            value_encrypted=encrypt(body.value),
            is_secret=body.is_secret,
            is_active=body.is_active,
        )
        session.add(item)
    else:
        item.value_encrypted = encrypt(body.value)
        item.is_secret = body.is_secret
        item.is_active = body.is_active
        item.updated_at = datetime.now(UTC)
    await session.flush()
    await write_audit_log(
        session,
        request,
        action="admin.provider_config_updated",
        resource_type="provider_config",
        resource_uuid=item.uuid,
        metadata={"provider": provider, "config_key": key},
    )
    await session.commit()
    return cr.success(data={"uuid": item.uuid}, message="Provider configuration saved")


@router.get("/feature-flags", response_model=CustomSuccessResponseSchema)
async def list_feature_flags(request: Request, session: AsyncSessionDep):
    _require(request)
    items = (
        (
            await session.execute(
                select(FeatureFlagModel).order_by(FeatureFlagModel.key.asc())
            )
        )
        .scalars()
        .all()
    )
    return cr.success(
        data={
            "items": [
                {
                    "uuid": item.uuid,
                    "key": item.key,
                    "description": item.description,
                    "is_enabled": item.is_enabled,
                    "rollout_percentage": item.rollout_percentage,
                    "organization_overrides": item.organization_overrides,
                }
                for item in items
            ]
        },
        message="Feature flags retrieved",
    )


@router.put("/feature-flags", response_model=CustomSuccessResponseSchema)
async def upsert_feature_flag(
    request: Request,
    body: FeatureFlagRequest,
    session: AsyncSessionDep,
):
    _require(request)
    item = (
        (
            await session.execute(
                select(FeatureFlagModel).where(FeatureFlagModel.key == body.key)
            )
        )
        .scalars()
        .first()
    )
    if not item:
        item = FeatureFlagModel(**body.model_dump())
        session.add(item)
    else:
        for key, value in body.model_dump().items():
            setattr(item, key, value)
        item.updated_at = datetime.now(UTC)
    await session.flush()
    await session.commit()
    return cr.success(
        data={"uuid": item.uuid, "key": item.key}, message="Feature flag saved"
    )


@router.put("/maintenance", response_model=CustomSuccessResponseSchema)
async def update_maintenance(
    request: Request,
    body: MaintenanceRequest,
    session: AsyncSessionDep,
):
    _require(request)
    item = (
        (
            await session.execute(
                select(PlatformSettingModel).where(
                    PlatformSettingModel.key == "maintenance"
                )
            )
        )
        .scalars()
        .first()
    )
    value = body.model_dump(mode="json")
    if not item:
        item = PlatformSettingModel(key="maintenance", value=value, is_public=True)
        session.add(item)
    else:
        item.value = value
        item.is_public = True
        item.updated_at = datetime.now(UTC)
    await session.commit()
    return cr.success(data=value, message="Maintenance setting updated")


@router.get("/domains", response_model=CustomSuccessResponseSchema)
async def list_domain_health(request: Request, session: AsyncSessionDep):
    _require(request)
    rows = (
        await session.execute(
            select(DomainHealthCheckModel, OrganizationModel.name)
            .join(
                OrganizationModel,
                OrganizationModel.id == DomainHealthCheckModel.organization_id,
            )
            .order_by(
                DomainHealthCheckModel.score.asc(),
                DomainHealthCheckModel.updated_at.desc(),
            )
        )
    ).all()
    return cr.success(
        data={
            "items": [
                {
                    "uuid": item.uuid,
                    "organization_name": organization_name,
                    "domain": item.domain,
                    "spf_status": item.spf_status,
                    "dkim_status": item.dkim_status,
                    "dmarc_status": item.dmarc_status,
                    "dns_status": item.dns_status,
                    "blacklist_status": item.blacklist_status,
                    "score": item.score,
                    "details": item.details,
                    "last_checked_at": item.last_checked_at,
                }
                for item, organization_name in rows
            ]
        },
        message="Domain health checks retrieved",
    )


@router.post(
    "/organizations/{organization_uuid}/domains/check",
    response_model=CustomSuccessResponseSchema,
)
async def run_domain_health_check(
    request: Request,
    organization_uuid: str,
    body: DomainHealthRequest,
    session: AsyncSessionDep,
):
    _require(request)
    organization = (
        (
            await session.execute(
                select(OrganizationModel).where(
                    OrganizationModel.uuid == organization_uuid
                )
            )
        )
        .scalars()
        .first()
    )
    if not organization:
        raise NotFoundError(error="Organization not found")
    result = await check_domain_health(body.domain, body.dkim_selectors)
    item = (
        (
            await session.execute(
                select(DomainHealthCheckModel).where(
                    DomainHealthCheckModel.organization_id == organization.id,
                    DomainHealthCheckModel.domain == result["domain"],
                )
            )
        )
        .scalars()
        .first()
    )
    values = {
        "spf_status": result["spf_status"],
        "dkim_status": result["dkim_status"],
        "dmarc_status": result["dmarc_status"],
        "dns_status": result["dns_status"],
        "blacklist_status": result["blacklist_status"],
        "score": result["score"],
        "details": result["details"],
        "last_checked_at": datetime.now(UTC),
    }
    if not item:
        item = DomainHealthCheckModel(
            organization_id=organization.id, domain=result["domain"], **values
        )
        session.add(item)
    else:
        for key, value in values.items():
            setattr(item, key, value)
        item.updated_at = datetime.now(UTC)
    await session.flush()
    await session.commit()
    return cr.success(
        data={"uuid": item.uuid, **result}, message="Domain health check completed"
    )


@router.get("/abuse-events", response_model=CustomSuccessResponseSchema)
async def list_abuse_events(
    request: Request,
    session: AsyncSessionDep,
    status: str | None = Query(default=None, max_length=30),
):
    _require(request)
    filters = []
    if status:
        filters.append(AbuseEventModel.status == status)
    rows = (
        await session.execute(
            select(AbuseEventModel, OrganizationModel.name, CampaignModel.uuid)
            .join(
                OrganizationModel,
                OrganizationModel.id == AbuseEventModel.organization_id,
            )
            .outerjoin(CampaignModel, CampaignModel.id == AbuseEventModel.campaign_id)
            .where(*filters)
            .order_by(AbuseEventModel.created_at.desc())
            .limit(200)
        )
    ).all()
    return cr.success(
        data={
            "items": [
                {
                    "uuid": item.uuid,
                    "organization_name": organization_name,
                    "campaign_uuid": campaign_uuid,
                    "severity": item.severity,
                    "reason": item.reason,
                    "status": item.status,
                    "metrics": item.metrics,
                    "created_at": item.created_at,
                }
                for item, organization_name, campaign_uuid in rows
            ]
        },
        message="Abuse events retrieved",
    )


@router.post("/abuse-events", response_model=CustomSuccessResponseSchema)
async def create_abuse_event(
    request: Request,
    body: AbuseEventRequest,
    session: AsyncSessionDep,
):
    _require(request)
    organization = (
        (
            await session.execute(
                select(OrganizationModel).where(
                    OrganizationModel.uuid == body.organization_uuid
                )
            )
        )
        .scalars()
        .first()
    )
    if not organization:
        raise NotFoundError(error="Organization not found")
    campaign_id = None
    if body.campaign_uuid:
        campaign = (
            (
                await session.execute(
                    select(CampaignModel).where(
                        CampaignModel.uuid == body.campaign_uuid,
                        CampaignModel.organization_id == organization.id,
                    )
                )
            )
            .scalars()
            .first()
        )
        if not campaign:
            raise NotFoundError(error="Campaign not found")
        campaign_id = campaign.id
    event = AbuseEventModel(
        organization_id=organization.id,
        campaign_id=campaign_id,
        severity=body.severity,
        reason=body.reason,
        metrics=body.metrics,
        status="open",
    )
    session.add(event)
    await session.flush()
    await session.commit()
    return cr.success(
        data={"uuid": event.uuid}, message="Abuse event created", status_code=201
    )


@router.post(
    "/abuse-events/{event_uuid}/suspend-campaign",
    response_model=CustomSuccessResponseSchema,
)
async def suspend_abusive_campaign(
    request: Request,
    event_uuid: str,
    session: AsyncSessionDep,
):
    _require(request)
    event = (
        (
            await session.execute(
                select(AbuseEventModel).where(AbuseEventModel.uuid == event_uuid)
            )
        )
        .scalars()
        .first()
    )
    if not event:
        raise NotFoundError(error="Abuse event not found")
    if not event.campaign_id:
        raise InvalidError(error="This abuse event is not linked to a campaign")
    campaign = await session.get(CampaignModel, event.campaign_id)
    if not campaign:
        raise NotFoundError(error="Campaign not found")
    now = datetime.now(UTC)
    campaign.status = "cancelled"
    campaign.cancelled_at = now
    campaign.updated_at = now
    event.status = "actioned"
    await write_audit_log(
        session,
        request,
        action="admin.abusive_campaign_suspended",
        resource_type="campaign",
        resource_uuid=campaign.uuid,
        metadata={"abuse_event_uuid": event.uuid},
        organization_id=event.organization_id,
    )
    await session.commit()
    return cr.success(
        data={"campaign_uuid": campaign.uuid, "status": campaign.status},
        message="Campaign suspended",
    )


@router.post(
    "/abuse-events/{event_uuid}/suspend-organization",
    response_model=CustomSuccessResponseSchema,
)
async def suspend_abusive_organization(
    request: Request,
    event_uuid: str,
    session: AsyncSessionDep,
):
    _require(request)
    event = (
        (
            await session.execute(
                select(AbuseEventModel).where(AbuseEventModel.uuid == event_uuid)
            )
        )
        .scalars()
        .first()
    )
    if not event:
        raise NotFoundError(error="Abuse event not found")
    organization = await session.get(OrganizationModel, event.organization_id)
    if not organization:
        raise NotFoundError(error="Organization not found")
    organization.status = "suspended"
    organization.updated_at = datetime.now(UTC)
    event.status = "actioned"
    await write_audit_log(
        session,
        request,
        action="admin.abusive_organization_suspended",
        resource_type="organization",
        resource_uuid=organization.uuid,
        metadata={"abuse_event_uuid": event.uuid},
        organization_id=organization.id,
    )
    await session.commit()
    return cr.success(
        data={"organization_uuid": organization.uuid, "status": organization.status},
        message="Organization suspended",
    )


@router.post(
    "/abuse-events/{event_uuid}/resolve", response_model=CustomSuccessResponseSchema
)
async def resolve_abuse_event(
    request: Request, event_uuid: str, session: AsyncSessionDep
):
    _require(request)
    event = (
        (
            await session.execute(
                select(AbuseEventModel).where(AbuseEventModel.uuid == event_uuid)
            )
        )
        .scalars()
        .first()
    )
    if not event:
        raise NotFoundError(error="Abuse event not found")
    event.status = "resolved"
    event.resolved_by_id = request.state.user_id
    event.resolved_at = datetime.now(UTC)
    await session.commit()
    return cr.success(
        data={"uuid": event.uuid, "status": event.status},
        message="Abuse event resolved",
    )
