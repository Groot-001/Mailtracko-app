# Feature implementation map

This document maps the supplied Phase 1 feature tracker to the implemented product areas. “Provider-backed” means the workflow is complete but requires the named credential or external account; it never falls back to generated results.

| Tracker area | Implemented capability | Primary implementation |
|---|---|---|
| Authentication & Security | Sign up, verification, login, password reset, new-IP suspicious login activity, 2FA, rate limiting, secure sessions | `backend/src/modules/auth`, public auth routes, security settings UI |
| Onboarding | Goal, volume, source, theme, organization profile and completion state | organization/onboarding backend use cases and protected onboarding routes |
| Email Account Setup | Gmail OAuth, custom SMTP/IMAP, credential preflight, verification, reconnect/disconnect, token refresh, health score, default/admin limits, signatures, encryption | `backend/src/modules/email_account`, sender-account UI |
| Contact Management | Lists, add/edit/delete, CSV import/export, persisted import errors, search/name/email/company/tag/list/status filters, organization duplicate protection, timeline/activity, individual/bulk verification, bounce risk, lifecycle states | `backend/src/modules/contacts`, contact dashboard/report/verification UI |
| Templates | CRUD, drafts, category/library, subject, rich/plain content, merge/custom fields, fallbacks, resolved preview, test send, opt-out variable | `backend/src/modules/email_template`, template wizard/gallery |
| Campaign Management | CRUD/duplicate/archive, audience/sender/template/sequence, immediate/scheduled send, pause/resume/cancel, timezone/window/days, daily/provider/account limits, recipient idempotency/progress, preflight variables/domain/risk, safe queueing | `backend/src/modules/campaign`, campaign wizard/dashboard/analytics |
| Team Management | Owner/admin/member roles, invitations/removal, owner-only role assignment, permission enforcement, team performance | organization module plus platform team endpoints and UI |
| Billing & Subscription | Current plan/limits, monthly/annual checkout, promotion coupon validation, audited upgrade/downgrade with configured proration, cancel/resume, trial conversion, usage counts, portal/payment method, failed-payment status, history/invoices/refunds, signed retry-safe webhook processing | platform billing models/routes, Stripe client/webhook event ledger, customer billing UI, superadmin Stripe/Price-ID panel |
| Settings, Security & Compliance | Organization/profile/timezone/theme, notification preferences, password/2FA/sessions, deactivation/deletion, audit log, suppression, signed one-click opt-out, send prevention, tenant isolation | auth/organization/platform modules and account-settings UI |
| Support & Help | Searchable published knowledge base/FAQ, email/live-chat entry points, tenant tickets, priority/status/messages/resolution, contextual domain/account-health search | platform support routes and support center |
| Super Admin Panel | Dashboard/revenue/infrastructure, users and organizations, plans/pricing/promotions, payments/transactions/refunds, abuse actions, domain/DNS/blacklist checks, support queue, encrypted provider config, feature flags, maintenance | `/api/v1/admin/*` control plane and protected admin console |

## Additional implemented integrations

- Google Sheets read-only OAuth, live worksheet discovery, import, and persisted import reports
- Workspace API keys stored as hashes and revealed once
- Workspace webhook endpoints with encrypted signing secrets
- In-app notifications and per-channel/category preferences
- Stripe and one-click unsubscribe public webhooks/endpoints

## Real configuration dependencies

| Capability | Required environment/configuration |
|---|---|
| Transactional email | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM` |
| Google sign-in | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, exact redirect URI |
| Gmail sender | `GOOGLE_MAIL_CLIENT_ID`, `GOOGLE_MAIL_CLIENT_SECRET`, exact redirect URI |
| Google Sheets | `GOOGLE_SHEETS_CLIENT_ID`, `GOOGLE_SHEETS_CLIENT_SECRET`, exact redirect URI |
| Contact verification | `BOUNCER_API_KEY` |
| Paid billing | `BILLING_ENABLED=true`, Stripe secret/webhook secret, monthly/annual plan Price IDs configured in the platform admin UI; follow `docs/STRIPE_SETUP.md` |
| Platform admin | `SUPERADMIN_EMAILS` as a JSON email list |
| Support channels | `PUBLIC_SUPPORT_EMAIL`, optional `CHATBOQ_WIDGET_URL` |
| Monitoring | optional `SENTRY_DSN`; platform dashboard checks PostgreSQL and Redis |

Empty provider values intentionally disable only the corresponding external workflow; they do not create fabricated results.
