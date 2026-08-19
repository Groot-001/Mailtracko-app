import hashlib
import hmac
import time
from unittest.mock import AsyncMock

import pytest

from src.modules.platform.application.stripe_client import (
    StripeClient,
    checkout_success_url,
    subscription_price_id,
    verify_stripe_signature,
)
from src.modules.platform.application.unsubscribe import (
    create_unsubscribe_token,
    read_unsubscribe_token,
)
from src.modules.platform.presentation.schemas import PlanRequest


def test_stripe_webhook_signature_accepts_valid_current_signature() -> None:
    payload = b'{"id":"evt_test","type":"invoice.paid"}'
    timestamp = int(time.time())
    secret = "whsec_test_value"
    signature = hmac.new(
        secret.encode(),
        f"{timestamp}.".encode() + payload,
        hashlib.sha256,
    ).hexdigest()

    assert verify_stripe_signature(
        payload,
        f"t={timestamp},v1={signature}",
        secret,
    )


def test_stripe_webhook_signature_rejects_tampered_payload() -> None:
    timestamp = int(time.time())
    signature = hmac.new(
        b"whsec_test_value",
        f"{timestamp}.".encode() + b"original",
        hashlib.sha256,
    ).hexdigest()

    assert not verify_stripe_signature(
        b"tampered",
        f"t={timestamp},v1={signature}",
        "whsec_test_value",
    )


def test_stripe_webhook_signature_rejects_expired_timestamp() -> None:
    payload = b'{"id":"evt_expired"}'
    timestamp = int(time.time()) - 301
    signature = hmac.new(
        b"whsec_test_value",
        f"{timestamp}.".encode() + payload,
        hashlib.sha256,
    ).hexdigest()

    assert not verify_stripe_signature(
        payload,
        f"t={timestamp},v1={signature}",
        "whsec_test_value",
    )


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://app.example.com/billing?checkout=success",
            "https://app.example.com/billing?checkout=success&session_id={CHECKOUT_SESSION_ID}",
        ),
        (
            "https://app.example.com/billing?session_id={CHECKOUT_SESSION_ID}",
            "https://app.example.com/billing?session_id={CHECKOUT_SESSION_ID}",
        ),
    ],
)
def test_checkout_success_url_adds_session_placeholder_once(
    url: str, expected: str
) -> None:
    assert checkout_success_url(url) == expected


def test_subscription_price_id_reads_first_recurring_item() -> None:
    assert (
        subscription_price_id(
            {"items": {"data": [{"price": {"id": "price_business_monthly"}}]}}
        )
        == "price_business_monthly"
    )
    assert subscription_price_id({"items": {"data": []}}) is None


@pytest.mark.asyncio
async def test_checkout_request_includes_subscription_metadata_and_idempotency() -> (
    None
):
    client = StripeClient("sk_test_mailtracko")
    client.request = AsyncMock(
        return_value={"id": "cs_test", "url": "https://checkout.stripe.com/test"}
    )

    result = await client.create_checkout_session(
        customer_id="cus_test",
        price_id="price_test",
        organization_uuid="org_test",
        plan_code="business",
        billing_cycle="annual",
        coupon_id="coupon_test",
        promotion_code="LAUNCH",
    )

    assert result["id"] == "cs_test"
    request = client.request.await_args
    assert request.args[:2] == ("POST", "checkout/sessions")
    assert (
        request.kwargs["data"]["subscription_data[metadata][organization_uuid]"]
        == "org_test"
    )
    assert request.kwargs["data"]["discounts[0][coupon]"] == "coupon_test"
    assert request.kwargs["idempotency_key"].startswith(
        "mailtracko-checkout-org_test-business-annual-"
    )


def test_plan_request_normalizes_currency_and_validates_stripe_price_ids() -> None:
    plan = PlanRequest(
        code="business",
        name="Business",
        currency="usd",
        stripe_monthly_price_id="price_monthly",
    )

    assert plan.currency == "USD"
    with pytest.raises(ValueError, match="must start with price_"):
        PlanRequest(
            code="invalid_price",
            name="Invalid Price",
            stripe_monthly_price_id="prod_not_a_price",
        )


def test_unsubscribe_token_round_trip_normalizes_email() -> None:
    token = create_unsubscribe_token(
        organization_id=42,
        email="  Recipient@Example.COM ",
    )

    payload = read_unsubscribe_token(token)

    assert payload == {"organization_id": 42, "email": "recipient@example.com"}
