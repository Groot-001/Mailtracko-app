import hashlib
import hmac
import time
from typing import Any

import httpx

from src.core.config.settings import config
from src.shared.exceptions.base_exceptions import InvalidError, ServerError


class StripeClient:
    base_url = "https://api.stripe.com/v1"

    def __init__(self, secret_key: str | None = None):
        self.secret_key = secret_key or config.STRIPE_SECRET_KEY

    def _ensure_configured(self) -> None:
        if not config.BILLING_ENABLED:
            raise InvalidError(error="Billing is not enabled for this deployment")
        if not self.secret_key:
            raise InvalidError(error="Billing provider credentials are not configured")

    async def request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        self._ensure_configured()
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        if config.STRIPE_API_VERSION:
            headers["Stripe-Version"] = config.STRIPE_API_VERSION
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.request(
                    method,
                    f"{self.base_url}/{path.lstrip('/')}",
                    data=data,
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            raise ServerError(
                error="Billing provider is unavailable",
                internal_details=str(exc),
            ) from exc

        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if response.status_code >= 400:
            message = (
                payload.get("error", {}).get("message")
                or "Billing provider request failed"
            )
            raise InvalidError(error=message)
        return payload

    async def create_customer(
        self, *, email: str, name: str, organization_uuid: str
    ) -> dict:
        return await self.request(
            "POST",
            "customers",
            data={
                "email": email,
                "name": name,
                "metadata[organization_uuid]": organization_uuid,
            },
            idempotency_key=f"mailtracko-customer-{organization_uuid}",
        )

    async def create_checkout_session(
        self,
        *,
        customer_id: str,
        price_id: str,
        organization_uuid: str,
        plan_code: str,
        billing_cycle: str,
        coupon_id: str | None = None,
        promotion_code: str | None = None,
    ) -> dict:
        data: dict[str, Any] = {
            "mode": "subscription",
            "customer": customer_id,
            "line_items[0][price]": price_id,
            "line_items[0][quantity]": 1,
            "success_url": checkout_success_url(config.STRIPE_SUCCESS_URL),
            "cancel_url": config.STRIPE_CANCEL_URL,
            "client_reference_id": organization_uuid,
            "metadata[organization_uuid]": organization_uuid,
            "metadata[plan_code]": plan_code,
            "metadata[billing_cycle]": billing_cycle,
            "subscription_data[metadata][organization_uuid]": organization_uuid,
            "subscription_data[metadata][plan_code]": plan_code,
            "subscription_data[metadata][billing_cycle]": billing_cycle,
            "allow_promotion_codes": "true" if not coupon_id else "false",
            "payment_method_collection": "always",
        }
        if config.STRIPE_COLLECT_BILLING_ADDRESS:
            data["billing_address_collection"] = "required"
            data["customer_update[address]"] = "auto"
            data["customer_update[name]"] = "auto"
        if config.STRIPE_AUTOMATIC_TAX:
            data["automatic_tax[enabled]"] = "true"
        if coupon_id:
            data["discounts[0][coupon]"] = coupon_id
        if promotion_code:
            data["metadata[promotion_code]"] = promotion_code
            data["subscription_data[metadata][promotion_code]"] = promotion_code
        return await self.request(
            "POST",
            "checkout/sessions",
            data=data,
            idempotency_key=(
                f"mailtracko-checkout-{organization_uuid}-{plan_code}-"
                f"{billing_cycle}-{int(time.time() // 300)}"
            ),
        )

    async def create_portal_session(self, customer_id: str) -> dict:
        return await self.request(
            "POST",
            "billing_portal/sessions",
            data={
                "customer": customer_id,
                "return_url": config.STRIPE_PORTAL_RETURN_URL,
            },
        )

    async def update_subscription(self, subscription_id: str, *, cancel: bool) -> dict:
        return await self.request(
            "POST",
            f"subscriptions/{subscription_id}",
            data={"cancel_at_period_end": "true" if cancel else "false"},
            idempotency_key=(
                f"mailtracko-cancel-{subscription_id}-{cancel}-"
                f"{int(time.time() // 300)}"
            ),
        )

    async def change_subscription_price(
        self,
        subscription_id: str,
        *,
        price_id: str,
        plan_code: str,
        billing_cycle: str,
        organization_uuid: str,
    ) -> dict:
        current = await self.request("GET", f"subscriptions/{subscription_id}")
        items = (current.get("items") or {}).get("data") or []
        if not items or not items[0].get("id"):
            raise InvalidError(error="The Stripe subscription has no editable item")
        return await self.request(
            "POST",
            f"subscriptions/{subscription_id}",
            data={
                "items[0][id]": items[0]["id"],
                "items[0][price]": price_id,
                "proration_behavior": config.STRIPE_PRORATION_BEHAVIOR,
                "cancel_at_period_end": "false",
                "metadata[organization_uuid]": organization_uuid,
                "metadata[plan_code]": plan_code,
                "metadata[billing_cycle]": billing_cycle,
            },
            idempotency_key=(
                f"mailtracko-plan-change-{subscription_id}-{price_id}-"
                f"{int(time.time() // 300)}"
            ),
        )

    async def create_refund(
        self,
        *,
        payment_intent_id: str,
        amount_cents: int | None,
        reason: str | None,
    ) -> dict:
        data: dict[str, Any] = {"payment_intent": payment_intent_id}
        if amount_cents is not None:
            data["amount"] = amount_cents
        if reason:
            data["reason"] = reason
        return await self.request(
            "POST",
            "refunds",
            data=data,
            idempotency_key=(
                f"mailtracko-refund-{payment_intent_id}-{amount_cents or 'full'}-"
                f"{reason or 'unspecified'}-{int(time.time() // 300)}"
            ),
        )


def checkout_success_url(url: str) -> str:
    """Add Stripe's Checkout Session placeholder once, preserving query strings."""

    if "{CHECKOUT_SESSION_ID}" in url:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}session_id={{CHECKOUT_SESSION_ID}}"


def subscription_price_id(subscription: dict[str, Any]) -> str | None:
    """Read the active recurring price from a Stripe subscription snapshot."""

    items = (subscription.get("items") or {}).get("data") or []
    if not items:
        return None
    price = items[0].get("price") or {}
    return price.get("id") if isinstance(price, dict) else None


def verify_stripe_signature(
    payload: bytes,
    signature_header: str,
    secret: str,
    *,
    tolerance_seconds: int = 300,
) -> bool:
    if not payload or not signature_header or not secret:
        return False
    values: dict[str, list[str]] = {}
    for item in signature_header.split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        values.setdefault(key.strip(), []).append(value.strip())
    timestamps = values.get("t", [])
    signatures = values.get("v1", [])
    if not timestamps or not signatures:
        return False
    try:
        timestamp = int(timestamps[0])
    except ValueError:
        return False
    if abs(int(time.time()) - timestamp) > tolerance_seconds:
        return False
    signed_payload = f"{timestamp}.".encode() + payload
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, signature) for signature in signatures)
