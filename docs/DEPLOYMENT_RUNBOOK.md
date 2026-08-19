# Production deployment runbook

## 1. Infrastructure

Provision:

- PostgreSQL 16 with encrypted storage, automated backups, and point-in-time recovery
- Redis 7 with authentication/TLS when it is outside the private application network
- Container runtime for frontend, API, migration job, campaign worker, and scheduler
- HTTPS ingress with the frontend at the public origin and `/api/` routed to FastAPI
- Central logs, error monitoring, uptime checks, and resource alerts

Run one scheduler replica. Workers can scale horizontally. Keep PostgreSQL and Redis private.

## 2. Create production secrets

Generate unique values outside source control:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Use the first value for `SECRET_KEY` and the second for `SECRET_ENCRYPTION_KEY`. Store all production values in the deployment platform's secret manager. Start from `backend/env/.example.production.env`, then provide those values to the Compose services as `.env.integration` or through the platform's environment injection.

Required production invariants:

```dotenv
ENVIRONMENT=production
DEBUG=false
APP_URL=https://app.your-domain.tld
FRONTEND_URL=https://app.your-domain.tld
CORS_ALLOWED_ORIGINS=["https://app.your-domain.tld"]
```

The API refuses to start if core production invariants are insecure. If the PostgreSQL password contains reserved URL characters (for example `@`, `:`, `/`, `%`, or `#`), URL-encode the password portion inside `DATABASE_URL`; keep `POSTGRES_PASSWORD` itself unencoded. The migration bootstrap safely escapes percent signs before passing the URL through Alembic.

## 3. Configure providers

Transactional SMTP:

- Verify the sending domain and publish SPF, DKIM, and DMARC.
- Set SMTP credentials and a verified `EMAIL_FROM`.
- Send registration, password-reset, and invitation test messages.

OAuth callback paths:

- Google sign-in: `/api/v1/auth/oauth/callback/google`
- Gmail sender: `/api/v1/email-accounts/oauth/callback/google`
- Google Sheets: `/api/v1/contact-lists/sheets/oauth/callback`

Register the exact HTTPS URLs at each provider. Configure separate development/staging/production OAuth applications where possible.

Stripe:

- Create products and monthly/annual prices.
- Configure plan price IDs through the protected platform administration UI.
- Set `BILLING_ENABLED=true` only after `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` are present.
- Register `POST https://<api-origin>/api/v1/billing/webhooks/stripe` for the exact checkout, subscription, invoice, payment, payment-method, and refund events listed in `docs/STRIPE_SETUP.md`.
- Complete a test-mode checkout, upgrade/downgrade, portal return, cancellation, failed payment, invoice download, and refund.
- Confirm repeated webhook delivery returns success and does not duplicate local records before switching to live keys.

Contact verification uses Bouncer through `BOUNCER_API_KEY` (and optional `BOUNCER_API_BASE_URL`). Verification is optional for campaign sending; without a key, verification controls are disabled while unverified contacts can still be used in campaigns.

Production organization/profile image uploads require Cloudinary. Configure `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET`; local development may use the persistent Docker upload volume instead.

Set `SUPERADMIN_EMAILS` to a JSON list of verified accounts. Platform administration is independent of workspace roles.

## 4. Deploy

Validate configuration without printing values:

```bash
./scripts/validate-environment.sh
```

Build and start:

```bash
docker compose pull
docker compose build --pull
docker compose up -d
```

The `migrate` service must exit successfully before the API starts. Confirm:

```bash
docker compose ps
curl -fsS https://api.your-domain.tld/openapi.json
curl -fsS https://app.your-domain.tld/
```

## 5. Staging acceptance

Use dedicated test recipients and verified sender accounts:

1. Register, verify email, log in, enable 2FA, and revoke a second session.
2. Complete onboarding and invite owner/admin/member roles.
3. Connect Gmail and custom SMTP/IMAP as applicable; run connection health checks.
4. Create/import contacts, verify individual/bulk addresses, and confirm invalid addresses enter suppression.
5. Create/test a template with standard/custom variables and fallbacks.
6. Launch immediate, scheduled, sequence, and A/B campaigns; verify limits, pause/resume, analytics, and no duplicate recipient sends.
7. Confirm unsubscribe immediately prevents later sends.
8. Complete Stripe checkout/portal/cancel/resume/refund flows and verify webhook-created billing records.
9. Create/reply/resolve support tickets and run domain/blacklist checks.
10. Verify platform user/organization suspension and an abuse-event campaign/organization action.

## 6. Backups and rollback

- Take a database snapshot immediately before migrations.
- Retain the previous application images for rollback.
- Application rollback: redeploy previous images. Do not downgrade the database unless the migration downgrade has been rehearsed on a restored staging snapshot.
- Data rollback: restore PostgreSQL to a new instance/point in time, validate it, then switch application connectivity.
- Rotate any credential suspected of exposure and invalidate active sessions if `SECRET_KEY` or account security is affected.

Document the release image digests, migration head, environment version, provider webhook delivery checks, and acceptance results for every production release.
