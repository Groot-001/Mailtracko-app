# Stripe billing setup

MailTracko uses Stripe-hosted Checkout for the first subscription, the Stripe Customer Portal for payment-method and invoice management, and server-side subscription updates for plan or billing-cycle changes. Signed webhooks are the source of truth for subscription, invoice, payment, card-summary, and refund state.

No Stripe credential is stored in the database or sent to the browser. Plan records contain only non-secret Stripe Price IDs.

## 1. Create test-mode products and prices

In Stripe test mode, create the product catalog you intend to sell. For every MailTracko plan that can be purchased, create:

- one recurring monthly Price;
- one recurring annual Price;
- the same three-letter currency used by the MailTracko plan.

Copy the `price_...` identifiers. Do not use Product IDs (`prod_...`) in plan fields.

## 2. Configure plan Price IDs

Sign in with a verified address listed in `SUPERADMIN_EMAILS`, open the platform administration page, and use **Stripe billing → Recurring plans**.

For each plan:

- set the displayed monthly and annual prices in the smallest currency unit;
- paste the monthly Stripe Price ID;
- paste the annual Stripe Price ID;
- set plan limits and feature labels;
- make the plan active;
- keep exactly one default plan for newly created workspaces.

A plan cycle without a Price ID remains visible but its checkout button is disabled. This prevents a customer from entering a broken payment flow.

## 3. Configure the server environment

Set the following values in the deployment secret manager. Keep billing disabled until the endpoint and prices are ready.

```dotenv
BILLING_ENABLED=false
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_API_VERSION=
STRIPE_AUTOMATIC_TAX=false
STRIPE_COLLECT_BILLING_ADDRESS=true
STRIPE_PRORATION_BEHAVIOR=create_prorations
STRIPE_SUCCESS_URL=https://app.your-domain.tld/organization/account-settings/billing?checkout=success
STRIPE_CANCEL_URL=https://app.your-domain.tld/organization/account-settings/billing?checkout=cancelled
STRIPE_PORTAL_RETURN_URL=https://app.your-domain.tld/organization/account-settings/billing
```

Notes:

- Hosted Checkout is created server-side, so the publishable key is not exposed or required by the current browser flow. It is still available for a future Stripe.js/Elements flow.
- Leaving `STRIPE_API_VERSION` empty uses the Stripe account default. If you pin it, validate that version in staging before production.
- `STRIPE_PRORATION_BEHAVIOR` accepts `create_prorations`, `always_invoice`, or `none`.
- Enable automatic tax only after Stripe Tax and customer-location collection are configured for the selling entity.

## 4. Register the signed webhook

Create a Stripe webhook destination at:

```text
POST https://api.your-domain.tld/api/v1/billing/webhooks/stripe
```

Subscribe to these events handled by the application:

```text
checkout.session.completed
customer.subscription.created
customer.subscription.updated
customer.subscription.deleted
customer.subscription.paused
customer.subscription.resumed
invoice.created
invoice.finalized
invoice.paid
invoice.payment_failed
invoice.payment_action_required
payment_intent.succeeded
payment_intent.payment_failed
payment_method.attached
charge.refunded
refund.updated
```

Copy the endpoint signing secret into `STRIPE_WEBHOOK_SECRET`. MailTracko validates the Stripe signature and timestamp before parsing the event, then stores the Stripe Event ID so retried deliveries are processed idempotently.

For local testing with Stripe CLI:

```bash
stripe login
stripe listen --forward-to localhost:8000/api/v1/billing/webhooks/stripe
```

Use the temporary `whsec_...` printed by the CLI only in the local environment.

## 5. Configure the Customer Portal

Enable the Stripe Customer Portal in test mode. Allow customers to update payment methods and view/download invoices. MailTracko performs application-controlled plan changes so local plan limits, audit logs, and Stripe metadata stay synchronized.

## 6. Test-mode acceptance

After migrations complete, set `BILLING_ENABLED=true`, restart the API, and verify the admin readiness panel shows the secret key, webhook signing secret, billing switch, and recurring Price IDs as configured.

Complete this checklist before using live keys:

1. Purchase a monthly plan through hosted Checkout.
2. Confirm the workspace subscription gets the Stripe customer/subscription IDs through webhooks.
3. Confirm the paid invoice and its hosted/PDF links appear in billing history.
4. Change to another plan and then change to annual billing; confirm the Stripe proration matches policy.
5. Open the Customer Portal and update the payment method.
6. Use a test card that requires authentication and one that fails; confirm local payment/subscription statuses update.
7. Schedule cancellation, resume it, then allow a test subscription to cancel.
8. Issue a full and partial refund from the administrator payment workflow and confirm the refund webhook state.
9. Replay a webhook event and confirm the endpoint returns success without duplicating billing records.
10. Review Stripe webhook delivery logs for a successful response to every selected event.

Stripe documents subscription state synchronization as asynchronous and recommends verified webhooks. See [Stripe subscription webhooks](https://docs.stripe.com/billing/subscriptions/webhooks), [webhook security and delivery](https://docs.stripe.com/webhooks), and [Customer Portal integration](https://docs.stripe.com/customer-management/integrate-customer-portal).

## 7. Move to live mode

Repeat the product/Price and webhook setup in live mode; Stripe test objects do not transfer to live mode. Replace all `sk_test_`, `pk_test_`, `whsec_`, and `price_` values with the live-mode values, re-run the full acceptance checklist with an approved real payment, and confirm refund/accounting behavior with the merchant owner.

Never paste Stripe keys into source files, browser environment variables, support tickets, logs, or the feature tracker.
