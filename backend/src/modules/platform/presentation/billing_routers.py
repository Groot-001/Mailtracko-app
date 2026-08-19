import json
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config.settings import config
from src.core.utils.response import CustomResponse as cr
from src.core.utils.response import CustomSuccessResponseSchema
from src.modules.campaign.infrastructure.models.campaign_models import (
    CampaignRecipientModel,
)
from src.modules.contacts.infrastructure.models.contact_models import ContactModel
from src.modules.email_account.infrastructure.models.email_account_model import (
    EmailAccountModel,
)
from src.modules.organization.infrastructure.models.organization_member_model import (
    OrganizationMemberModel,
)
from src.modules.organization.infrastructure.models.organization_model import (
    OrganizationModel,
)
from src.modules.platform.application.access import (
    load_workspace_context,
    write_audit_log,
)
from src.modules.platform.application.stripe_client import (
    StripeClient,
    subscription_price_id,
    verify_stripe_signature,
)
from src.modules.platform.infrastructure.models.platform_models import (
    BillingPlanModel,
    BillingProfileModel,
    InvoiceModel,
    PaymentModel,
    PromotionModel,
    RefundModel,
    StripeWebhookEventModel,
    SubscriptionModel,
)
from src.modules.platform.presentation.schemas import (
    BillingProfileRequest,
    CheckoutRequest,
)
from src.shared.dependencies.access_guard import require_access
from src.shared.exceptions.base_exceptions import InvalidError, NotFoundError
from src.shared.infrastructure.db import get_async_session

protected_router = APIRouter(
    prefix="/billing",
    dependencies=[Depends(require_access(authenticated=True, email_verified=True))],
)
public_router = APIRouter(prefix="/billing")
router = APIRouter()
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


def _timestamp(value: int | None) -> datetime | None:
    return datetime.fromtimestamp(value, UTC) if value else None


def _invoice_payment_intent_id(invoice: dict) -> str | None:
    if invoice.get("payment_intent"):
        return str(invoice["payment_intent"])
    payments = (invoice.get("payments") or {}).get("data") or []
    for payment in payments:
        payment_details = payment.get("payment") or {}
        if payment_details.get("payment_intent"):
            return str(payment_details["payment_intent"])
    return None


def _plan_payload(plan: BillingPlanModel) -> dict:
    return {
        "uuid": plan.uuid,
        "code": plan.code,
        "name": plan.name,
        "description": plan.description,
        "currency": plan.currency,
        "monthly_price_cents": plan.monthly_price_cents,
        "annual_price_cents": plan.annual_price_cents,
        "trial_days": plan.trial_days,
        "limits": plan.limits or {},
        "features": plan.features or [],
        "is_active": plan.is_active,
        "is_default": plan.is_default,
        "display_order": plan.display_order,
        "monthly_checkout_configured": bool(plan.stripe_monthly_price_id),
        "annual_checkout_configured": bool(plan.stripe_annual_price_id),
    }


def _subscription_payload(
    subscription: SubscriptionModel, plan: BillingPlanModel
) -> dict:
    return {
        "uuid": subscription.uuid,
        "status": subscription.status,
        "billing_cycle": subscription.billing_cycle,
        "seats": subscription.seats,
        "trial_ends_at": subscription.trial_ends_at,
        "current_period_start": subscription.current_period_start,
        "current_period_end": subscription.current_period_end,
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "canceled_at": subscription.canceled_at,
        "provider_managed": bool(subscription.provider_subscription_id),
        "plan": _plan_payload(plan),
    }


async def _get_or_create_default_subscription(
    session: AsyncSession,
    organization_id: int,
) -> tuple[SubscriptionModel | None, BillingPlanModel | None]:
    subscription = (
        (
            await session.execute(
                select(SubscriptionModel).where(
                    SubscriptionModel.organization_id == organization_id
                )
            )
        )
        .scalars()
        .first()
    )
    if subscription:
        plan = await session.get(BillingPlanModel, subscription.plan_id)
        return subscription, plan

    plan = (
        (
            await session.execute(
                select(BillingPlanModel)
                .where(
                    BillingPlanModel.is_default.is_(True),
                    BillingPlanModel.is_active.is_(True),
                )
                .order_by(
                    BillingPlanModel.display_order.asc(), BillingPlanModel.id.asc()
                )
            )
        )
        .scalars()
        .first()
    )
    if not plan:
        return None, None

    trial_ends_at = (
        datetime.now(UTC) + timedelta(days=plan.trial_days) if plan.trial_days else None
    )
    subscription = SubscriptionModel(
        organization_id=organization_id,
        plan_id=plan.id,
        status="trialing" if trial_ends_at else "active",
        billing_cycle="monthly",
        seats=1,
        trial_ends_at=trial_ends_at,
        current_period_start=datetime.now(UTC),
        current_period_end=trial_ends_at,
    )
    session.add(subscription)
    await session.flush()
    return subscription, plan


async def _usage(session: AsyncSession, organization_id: int) -> dict:
    contacts = (
        await session.execute(
            select(func.count(ContactModel.id)).where(
                ContactModel.organization_id == organization_id
            )
        )
    ).scalar() or 0
    sends = (
        await session.execute(
            select(func.count(CampaignRecipientModel.id)).where(
                CampaignRecipientModel.organization_id == organization_id,
                CampaignRecipientModel.sent_at.is_not(None),
            )
        )
    ).scalar() or 0
    sender_accounts = (
        await session.execute(
            select(func.count(EmailAccountModel.id)).where(
                EmailAccountModel.organization_id == organization_id,
                EmailAccountModel.deleted_at.is_(None),
            )
        )
    ).scalar() or 0
    team_members = (
        await session.execute(
            select(func.count(OrganizationMemberModel.id)).where(
                OrganizationMemberModel.organization_id == organization_id,
                OrganizationMemberModel.status == "active",
                OrganizationMemberModel.deleted_at.is_(None),
            )
        )
    ).scalar() or 0
    return {
        "contacts": contacts,
        "sends": sends,
        "sender_accounts": sender_accounts,
        "team_members": team_members,
    }


@protected_router.get("/plans", response_model=CustomSuccessResponseSchema)
async def list_plans(session: AsyncSessionDep):
    plans = (
        (
            await session.execute(
                select(BillingPlanModel)
                .where(BillingPlanModel.is_active.is_(True))
                .order_by(
                    BillingPlanModel.display_order.asc(), BillingPlanModel.id.asc()
                )
            )
        )
        .scalars()
        .all()
    )
    return cr.success(
        data={"items": [_plan_payload(plan) for plan in plans]},
        message="Plans retrieved",
    )


@protected_router.get("/overview", response_model=CustomSuccessResponseSchema)
async def billing_overview(request: Request, session: AsyncSessionDep):
    context = await load_workspace_context(request, session)
    subscription, plan = await _get_or_create_default_subscription(
        session, context.organization.id
    )
    profile = (
        (
            await session.execute(
                select(BillingProfileModel).where(
                    BillingProfileModel.organization_id == context.organization.id
                )
            )
        )
        .scalars()
        .first()
    )
    invoices = (
        (
            await session.execute(
                select(InvoiceModel)
                .where(InvoiceModel.organization_id == context.organization.id)
                .order_by(InvoiceModel.created_at.desc())
                .limit(50)
            )
        )
        .scalars()
        .all()
    )
    available_plans = (
        (
            await session.execute(
                select(BillingPlanModel)
                .where(BillingPlanModel.is_active.is_(True))
                .order_by(BillingPlanModel.display_order.asc())
            )
        )
        .scalars()
        .all()
    )
    usage = await _usage(session, context.organization.id)
    await session.commit()

    profile_payload = None
    if profile:
        profile_payload = {
            "billing_email": profile.billing_email,
            "company_name": profile.company_name,
            "tax_id": profile.tax_id,
            "address": profile.address,
            "card_brand": profile.card_brand,
            "card_last4": profile.card_last4,
            "card_exp_month": profile.card_exp_month,
            "card_exp_year": profile.card_exp_year,
        }
    invoice_payload = [
        {
            "uuid": invoice.uuid,
            "number": invoice.number,
            "description": invoice.description,
            "amount_due_cents": invoice.amount_due_cents,
            "amount_paid_cents": invoice.amount_paid_cents,
            "currency": invoice.currency,
            "status": invoice.status,
            "hosted_invoice_url": invoice.hosted_invoice_url,
            "invoice_pdf_url": invoice.invoice_pdf_url,
            "period_start": invoice.period_start,
            "period_end": invoice.period_end,
            "paid_at": invoice.paid_at,
            "created_at": invoice.created_at,
        }
        for invoice in invoices
    ]
    return cr.success(
        data={
            "billing_enabled": config.BILLING_ENABLED,
            "subscription": _subscription_payload(subscription, plan)
            if subscription and plan
            else None,
            "available_plans": [_plan_payload(item) for item in available_plans],
            "usage": usage,
            "limits": plan.limits if plan else {},
            "profile": profile_payload,
            "invoices": invoice_payload,
        },
        message="Billing overview retrieved",
    )


@protected_router.put("/profile", response_model=CustomSuccessResponseSchema)
async def update_billing_profile(
    request: Request,
    body: BillingProfileRequest,
    session: AsyncSessionDep,
):
    context = await load_workspace_context(request, session, {"owner", "admin"})
    profile = (
        (
            await session.execute(
                select(BillingProfileModel).where(
                    BillingProfileModel.organization_id == context.organization.id
                )
            )
        )
        .scalars()
        .first()
    )
    values = body.model_dump(exclude_unset=True)
    if not profile:
        profile = BillingProfileModel(organization_id=context.organization.id, **values)
        session.add(profile)
    else:
        for key, value in values.items():
            setattr(profile, key, value)
        profile.updated_at = datetime.now(UTC)
    await write_audit_log(
        session,
        request,
        action="billing.profile_updated",
        resource_type="billing_profile",
        resource_uuid=profile.uuid,
        organization_id=context.organization.id,
    )
    await session.commit()
    return cr.success(
        data={"uuid": profile.uuid, **values}, message="Billing profile updated"
    )


@protected_router.post("/checkout", response_model=CustomSuccessResponseSchema)
async def create_checkout(
    request: Request,
    body: CheckoutRequest,
    session: AsyncSessionDep,
):
    context = await load_workspace_context(request, session, {"owner", "admin"})
    plan = (
        (
            await session.execute(
                select(BillingPlanModel).where(
                    BillingPlanModel.code == body.plan_code,
                    BillingPlanModel.is_active.is_(True),
                )
            )
        )
        .scalars()
        .first()
    )
    if not plan:
        raise NotFoundError(error="Subscription plan not found")
    price_id = (
        plan.stripe_annual_price_id
        if body.billing_cycle == "annual"
        else plan.stripe_monthly_price_id
    )
    if not price_id:
        raise InvalidError(
            error="The selected plan is not configured for provider checkout"
        )

    promotion = None
    now = datetime.now(UTC)
    if body.promotion_code:
        promotion = (
            (
                await session.execute(
                    select(PromotionModel).where(
                        func.lower(PromotionModel.code)
                        == body.promotion_code.strip().lower(),
                        PromotionModel.is_active.is_(True),
                    )
                )
            )
            .scalars()
            .first()
        )
        if not promotion:
            raise InvalidError(error="Promotion code is invalid")
        if promotion.starts_at and promotion.starts_at > now:
            raise InvalidError(error="Promotion is not active yet")
        if promotion.ends_at and promotion.ends_at <= now:
            raise InvalidError(error="Promotion has expired")
        if (
            promotion.max_redemptions
            and promotion.redemption_count >= promotion.max_redemptions
        ):
            raise InvalidError(error="Promotion redemption limit has been reached")
        if not promotion.provider_coupon_id:
            raise InvalidError(error="Promotion is not configured with a Stripe coupon")

    subscription, _ = await _get_or_create_default_subscription(
        session, context.organization.id
    )
    if not subscription:
        raise InvalidError(error="No default subscription configuration is available")
    if subscription.provider_subscription_id:
        raise InvalidError(
            error="This workspace already has a Stripe subscription; use the plan-change endpoint"
        )
    customer_id = subscription.provider_customer_id
    stripe = StripeClient()
    if not customer_id:
        customer = await stripe.create_customer(
            email=request.state.user.email,
            name=context.organization.name,
            organization_uuid=context.organization.uuid,
        )
        customer_id = customer["id"]
        subscription.provider_customer_id = customer_id

    checkout = await stripe.create_checkout_session(
        customer_id=customer_id,
        price_id=price_id,
        organization_uuid=context.organization.uuid,
        plan_code=plan.code,
        billing_cycle=body.billing_cycle,
        coupon_id=promotion.provider_coupon_id if promotion else None,
        promotion_code=promotion.code if promotion else None,
    )
    await write_audit_log(
        session,
        request,
        action="billing.checkout_created",
        resource_type="subscription",
        resource_uuid=subscription.uuid,
        metadata={"plan_code": plan.code, "billing_cycle": body.billing_cycle},
        organization_id=context.organization.id,
    )
    await session.commit()
    return cr.success(
        data={"checkout_url": checkout.get("url")}, message="Checkout created"
    )


@protected_router.post("/change-plan", response_model=CustomSuccessResponseSchema)
async def change_subscription_plan(
    request: Request,
    body: CheckoutRequest,
    session: AsyncSessionDep,
):
    context = await load_workspace_context(request, session, {"owner", "admin"})
    subscription = (
        (
            await session.execute(
                select(SubscriptionModel).where(
                    SubscriptionModel.organization_id == context.organization.id
                )
            )
        )
        .scalars()
        .first()
    )
    if not subscription or not subscription.provider_subscription_id:
        raise InvalidError(error="No Stripe subscription exists for this workspace")
    plan = (
        (
            await session.execute(
                select(BillingPlanModel).where(
                    BillingPlanModel.code == body.plan_code,
                    BillingPlanModel.is_active.is_(True),
                )
            )
        )
        .scalars()
        .first()
    )
    if not plan:
        raise NotFoundError(error="Subscription plan not found")
    if (
        subscription.plan_id == plan.id
        and subscription.billing_cycle == body.billing_cycle
    ):
        raise InvalidError(
            error="The workspace already uses this plan and billing cycle"
        )
    price_id = (
        plan.stripe_annual_price_id
        if body.billing_cycle == "annual"
        else plan.stripe_monthly_price_id
    )
    if not price_id:
        raise InvalidError(
            error="The selected billing cycle is not configured in Stripe"
        )

    result = await StripeClient().change_subscription_price(
        subscription.provider_subscription_id,
        price_id=price_id,
        plan_code=plan.code,
        billing_cycle=body.billing_cycle,
        organization_uuid=context.organization.uuid,
    )
    subscription.plan_id = plan.id
    subscription.billing_cycle = body.billing_cycle
    subscription.status = result.get("status") or subscription.status
    subscription.cancel_at_period_end = bool(result.get("cancel_at_period_end", False))
    subscription.current_period_start = _timestamp(result.get("current_period_start"))
    subscription.current_period_end = _timestamp(result.get("current_period_end"))
    subscription.updated_at = datetime.now(UTC)
    await write_audit_log(
        session,
        request,
        action="billing.subscription_plan_changed",
        resource_type="subscription",
        resource_uuid=subscription.uuid,
        metadata={"plan_code": plan.code, "billing_cycle": body.billing_cycle},
        organization_id=context.organization.id,
    )
    await session.commit()
    return cr.success(
        data={
            "plan_code": plan.code,
            "billing_cycle": body.billing_cycle,
            "status": subscription.status,
        },
        message="Subscription plan updated",
    )


@protected_router.post("/portal", response_model=CustomSuccessResponseSchema)
async def create_customer_portal(request: Request, session: AsyncSessionDep):
    context = await load_workspace_context(request, session, {"owner", "admin"})
    subscription = (
        (
            await session.execute(
                select(SubscriptionModel).where(
                    SubscriptionModel.organization_id == context.organization.id
                )
            )
        )
        .scalars()
        .first()
    )
    if not subscription or not subscription.provider_customer_id:
        raise InvalidError(error="No billing customer exists for this workspace")
    portal = await StripeClient().create_portal_session(
        subscription.provider_customer_id
    )
    return cr.success(
        data={"portal_url": portal.get("url")}, message="Billing portal created"
    )


async def _set_cancellation(
    request: Request,
    session: AsyncSession,
    *,
    cancel: bool,
):
    context = await load_workspace_context(request, session, {"owner"})
    subscription = (
        (
            await session.execute(
                select(SubscriptionModel).where(
                    SubscriptionModel.organization_id == context.organization.id
                )
            )
        )
        .scalars()
        .first()
    )
    if not subscription or not subscription.provider_subscription_id:
        raise InvalidError(error="No paid subscription exists for this workspace")
    result = await StripeClient().update_subscription(
        subscription.provider_subscription_id,
        cancel=cancel,
    )
    subscription.cancel_at_period_end = bool(result.get("cancel_at_period_end", cancel))
    subscription.updated_at = datetime.now(UTC)
    await write_audit_log(
        session,
        request,
        action="billing.subscription_cancel_requested"
        if cancel
        else "billing.subscription_resumed",
        resource_type="subscription",
        resource_uuid=subscription.uuid,
        organization_id=context.organization.id,
    )
    await session.commit()
    return cr.success(
        data={"cancel_at_period_end": subscription.cancel_at_period_end},
        message="Subscription cancellation scheduled"
        if cancel
        else "Subscription resumed",
    )


@protected_router.post("/cancel", response_model=CustomSuccessResponseSchema)
async def cancel_subscription(request: Request, session: AsyncSessionDep):
    return await _set_cancellation(request, session, cancel=True)


@protected_router.post("/resume", response_model=CustomSuccessResponseSchema)
async def resume_subscription(request: Request, session: AsyncSessionDep):
    return await _set_cancellation(request, session, cancel=False)


@public_router.post("/webhooks/stripe", response_model=CustomSuccessResponseSchema)
async def stripe_webhook(
    request: Request,
    session: AsyncSessionDep,
    stripe_signature: Annotated[str | None, Header(alias="Stripe-Signature")] = None,
):
    raw = await request.body()
    if not verify_stripe_signature(
        raw,
        stripe_signature or "",
        config.STRIPE_WEBHOOK_SECRET,
    ):
        raise InvalidError(error="Invalid billing webhook signature")
    try:
        event = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InvalidError(error="Invalid webhook payload") from exc

    event_id = str(event.get("id") or "")
    if not event_id:
        raise InvalidError(error="Stripe webhook event ID is missing")
    already_processed = (
        (
            await session.execute(
                select(StripeWebhookEventModel).where(
                    StripeWebhookEventModel.provider_event_id == event_id
                )
            )
        )
        .scalars()
        .first()
    )
    if already_processed:
        return cr.success(
            data={"received": True, "duplicate": True},
            message="Webhook already processed",
        )

    event_type = event.get("type", "")
    session.add(
        StripeWebhookEventModel(
            provider_event_id=event_id,
            event_type=event_type or "unknown",
            livemode=bool(event.get("livemode", False)),
            api_version=event.get("api_version"),
            processed_at=datetime.now(UTC),
        )
    )
    obj = event.get("data", {}).get("object", {})
    metadata = obj.get("metadata") or {}
    organization_uuid = metadata.get("organization_uuid") or obj.get(
        "client_reference_id"
    )
    organization = None
    if organization_uuid:
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

    if event_type == "checkout.session.completed" and organization:
        plan_code = metadata.get("plan_code")
        plan = (
            (
                await session.execute(
                    select(BillingPlanModel).where(BillingPlanModel.code == plan_code)
                )
            )
            .scalars()
            .first()
        )
        subscription, _ = await _get_or_create_default_subscription(
            session, organization.id
        )
        if subscription and plan:
            subscription.plan_id = plan.id
            subscription.status = "active"
            subscription.billing_cycle = metadata.get("billing_cycle", "monthly")
            subscription.provider_customer_id = obj.get("customer")
            subscription.provider_subscription_id = obj.get("subscription")
            subscription.cancel_at_period_end = False
            promotion_code = metadata.get("promotion_code")
            if promotion_code:
                promotion = (
                    (
                        await session.execute(
                            select(PromotionModel).where(
                                func.lower(PromotionModel.code)
                                == str(promotion_code).lower()
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if promotion and subscription.promotion_id != promotion.id:
                    subscription.promotion_id = promotion.id
                    promotion.redemption_count += 1

    elif event_type.startswith("customer.subscription."):
        provider_subscription_id = obj.get("id")
        subscription = (
            (
                await session.execute(
                    select(SubscriptionModel).where(
                        SubscriptionModel.provider_subscription_id
                        == provider_subscription_id
                    )
                )
            )
            .scalars()
            .first()
        )
        if not subscription and organization:
            subscription, _ = await _get_or_create_default_subscription(
                session, organization.id
            )
            if subscription:
                subscription.provider_subscription_id = provider_subscription_id
                subscription.provider_customer_id = obj.get("customer")
        if subscription:
            price_id = subscription_price_id(obj)
            plan_code = metadata.get("plan_code")
            if price_id:
                plan = (
                    (
                        await session.execute(
                            select(BillingPlanModel).where(
                                or_(
                                    BillingPlanModel.stripe_monthly_price_id
                                    == price_id,
                                    BillingPlanModel.stripe_annual_price_id == price_id,
                                )
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if plan:
                    subscription.plan_id = plan.id
                    subscription.billing_cycle = (
                        "annual"
                        if plan.stripe_annual_price_id == price_id
                        else "monthly"
                    )
            elif plan_code:
                plan = (
                    (
                        await session.execute(
                            select(BillingPlanModel).where(
                                BillingPlanModel.code == plan_code
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if plan:
                    subscription.plan_id = plan.id
            subscription.status = (
                "canceled"
                if event_type.endswith("deleted")
                else obj.get("status", subscription.status)
            )
            if not price_id:
                subscription.billing_cycle = metadata.get(
                    "billing_cycle", subscription.billing_cycle
                )
            subscription.current_period_start = _timestamp(
                obj.get("current_period_start")
            )
            subscription.current_period_end = _timestamp(obj.get("current_period_end"))
            subscription.trial_ends_at = _timestamp(obj.get("trial_end"))
            subscription.cancel_at_period_end = bool(
                obj.get("cancel_at_period_end", False)
            )
            subscription.canceled_at = _timestamp(obj.get("canceled_at"))

    elif event_type.startswith("invoice."):
        customer_id = obj.get("customer")
        subscription = (
            (
                await session.execute(
                    select(SubscriptionModel).where(
                        SubscriptionModel.provider_customer_id == customer_id
                    )
                )
            )
            .scalars()
            .first()
        )
        if subscription:
            invoice = (
                (
                    await session.execute(
                        select(InvoiceModel).where(
                            InvoiceModel.provider_invoice_id == obj.get("id")
                        )
                    )
                )
                .scalars()
                .first()
            )
            if not invoice:
                invoice = InvoiceModel(
                    organization_id=subscription.organization_id,
                    subscription_id=subscription.id,
                    provider_invoice_id=obj.get("id"),
                    status=obj.get("status") or "open",
                )
                session.add(invoice)
            invoice.number = obj.get("number")
            invoice.description = obj.get("description")
            invoice.amount_due_cents = int(obj.get("amount_due") or 0)
            invoice.amount_paid_cents = int(obj.get("amount_paid") or 0)
            invoice.currency = str(obj.get("currency") or "usd").upper()
            invoice.status = obj.get("status") or invoice.status
            invoice.hosted_invoice_url = obj.get("hosted_invoice_url")
            invoice.invoice_pdf_url = obj.get("invoice_pdf")
            invoice.period_start = _timestamp(obj.get("period_start"))
            invoice.period_end = _timestamp(obj.get("period_end"))
            invoice.paid_at = _timestamp(
                (obj.get("status_transitions") or {}).get("paid_at")
            )
            await session.flush()

            payment_intent = _invoice_payment_intent_id(obj)
            payment_events = {
                "invoice.paid": "paid",
                "invoice.payment_failed": "failed",
                "invoice.payment_action_required": "requires_action",
            }
            payment_status = payment_events.get(event_type)
            if payment_intent and payment_status:
                payment = (
                    (
                        await session.execute(
                            select(PaymentModel).where(
                                PaymentModel.provider_payment_intent_id
                                == payment_intent
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if not payment:
                    payment = PaymentModel(
                        organization_id=subscription.organization_id,
                        invoice_id=invoice.id,
                        provider_payment_intent_id=payment_intent,
                        amount_cents=invoice.amount_paid_cents
                        or invoice.amount_due_cents,
                        currency=invoice.currency,
                        status=payment_status,
                    )
                    session.add(payment)
                else:
                    payment.status = payment_status
                    payment.amount_cents = (
                        invoice.amount_paid_cents or invoice.amount_due_cents
                    )
                if payment_status in {"failed", "requires_action"}:
                    subscription.status = "past_due"

    elif event_type in {"payment_intent.succeeded", "payment_intent.payment_failed"}:
        payment = (
            (
                await session.execute(
                    select(PaymentModel).where(
                        PaymentModel.provider_payment_intent_id == obj.get("id")
                    )
                )
            )
            .scalars()
            .first()
        )
        if payment:
            payment.status = "paid" if event_type.endswith("succeeded") else "failed"
            last_error = obj.get("last_payment_error") or {}
            payment.failure_message = (
                None
                if event_type.endswith("succeeded")
                else last_error.get("message") or "Payment failed"
            )

    elif event_type == "payment_method.attached":
        customer_id = obj.get("customer")
        subscription = (
            (
                await session.execute(
                    select(SubscriptionModel).where(
                        SubscriptionModel.provider_customer_id == customer_id
                    )
                )
            )
            .scalars()
            .first()
        )
        card = obj.get("card") or {}
        if subscription and card:
            profile = (
                (
                    await session.execute(
                        select(BillingProfileModel).where(
                            BillingProfileModel.organization_id
                            == subscription.organization_id
                        )
                    )
                )
                .scalars()
                .first()
            )
            if not profile:
                profile = BillingProfileModel(
                    organization_id=subscription.organization_id
                )
                session.add(profile)
            profile.card_brand = card.get("brand")
            profile.card_last4 = card.get("last4")
            profile.card_exp_month = card.get("exp_month")
            profile.card_exp_year = card.get("exp_year")

    elif event_type in {"charge.refunded", "refund.updated"}:
        payment_intent_id = obj.get("payment_intent")
        payment = (
            (
                await session.execute(
                    select(PaymentModel).where(
                        PaymentModel.provider_payment_intent_id == payment_intent_id
                    )
                )
            )
            .scalars()
            .first()
        )
        if payment:
            refund_items = (
                ((obj.get("refunds") or {}).get("data") or [])
                if event_type == "charge.refunded"
                else [obj]
            )
            for item in refund_items:
                provider_refund_id = item.get("id")
                if not provider_refund_id:
                    continue
                refund = (
                    (
                        await session.execute(
                            select(RefundModel).where(
                                RefundModel.provider_refund_id == provider_refund_id
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if not refund:
                    refund = RefundModel(
                        organization_id=payment.organization_id,
                        payment_id=payment.id,
                        provider_refund_id=provider_refund_id,
                        amount_cents=int(item.get("amount") or 0),
                        status=item.get("status") or "pending",
                        reason=item.get("reason"),
                    )
                    session.add(refund)
                else:
                    refund.status = item.get("status") or refund.status
                    refund.amount_cents = int(item.get("amount") or refund.amount_cents)
            if event_type == "charge.refunded":
                payment.refunded_cents = int(obj.get("amount_refunded") or 0)
                if obj.get("refunded"):
                    payment.status = "refunded"

    await session.commit()
    return cr.success(data={"received": True}, message="Webhook processed")


router.include_router(public_router)
router.include_router(protected_router)
