# MailTracko SaaS

MailTracko is a multi-tenant email outreach SaaS built with FastAPI, PostgreSQL, Redis, Dramatiq, React, TypeScript, TanStack Router/Query, and Tailwind CSS.

The release contains real persistence and provider integrations. It does not seed customer accounts, campaigns, contacts, tickets, invoices, or dashboard metrics. Provider-backed actions clearly require configuration when credentials are absent.

## Product areas

- Authentication, email verification, password recovery, suspicious-login activity, 2FA, and session revocation
- Workspace onboarding, organization settings, team invitations, roles, and performance
- Gmail OAuth plus encrypted custom SMTP/IMAP sender accounts and health monitoring
- Contact lists, CRUD, CSV/Google Sheets import, export, import reports, timeline, verification, lifecycle status, and suppression
- Templates, variables/fallbacks, rich/plain content, preview, test sending, and opt-out insertion
- Campaigns, sequences, A/B tests, schedules, timezones, sending windows, layered limits, review, queueing, delivery, and analytics
- Stripe-hosted checkout, audited plan/cycle changes, cancellation/resume, customer portal, invoices, payments, refunds, usage, and idempotent signed webhook synchronization
- Notifications, audit logs, API keys, webhook endpoints, compliance, one-click unsubscribe, and tenant isolation
- Knowledge base, support tickets, email/live-chat entry points, and administrator ticket workflow
- Platform administration for users, organizations, plans, promotions, billing, abuse, domains, providers, feature flags, and maintenance

## Run locally with REAL Gmail delivery

Requirements: Docker Desktop / Docker Engine with Compose v2, a Gmail or Google Workspace account with 2-Step Verification, and a Google App Password.

This package intentionally does **not** include a local SMTP catcher. Verification codes, password-reset messages, invitations, and other transactional mail are configured to leave MailTracko through `smtp.gmail.com`.

1. If you are upgrading from an already-working local MailTracko folder and want to keep its Docker database, first import its existing environment so the PostgreSQL password and Fernet key remain stable:

   ```powershell
   .\scripts\import-existing-local-env.ps1 -FromProject "C:\path\to\old-MailTracko-folder"
   ```

   Skip this step for a fresh local database.

2. Configure real Gmail SMTP and generate/preserve local secrets:

   **Windows PowerShell**

   ```powershell
   .\scripts\configure-local.ps1
   ```

   **Linux/macOS**

   ```bash
   ./scripts/configure-local.sh
   ```

   Use a **Google App Password**, not your normal Google account password. Do not share the App Password in chat or commit `.env.integration`.

3. Start the stack with fail-fast runtime validation:

   ```powershell
   .\scripts\start-local.ps1
   ```

   or:

   ```bash
   ./scripts/start-local.sh
   ```

   The `configcheck` container validates real SMTP, the database URL, the Fernet encryption key, and production storage requirements before migrations/API startup. This prevents malformed credentials from surfacing later as crash loops.

4. Prove real delivery before testing registration:

   ```powershell
   .\scripts\test-real-email.ps1
   ```

   or:

   ```bash
   ./scripts/test-real-email.sh
   ```

5. Open the product at `http://127.0.0.1:3000` and API documentation at `http://127.0.0.1:8000/docs`. Register using a different real email address and confirm the **first** verification code arrives without pressing Resend.

6. Configure provider-backed QA features when you are ready to test them:

   ```powershell
   .\scripts\configure-integrations.ps1
   ```

   This can set Google OAuth (login, Gmail sender, and Google Sheets), Bouncer, Cloudinary, and a verified Platform Admin email without printing secret values. Local logo/profile uploads work through persistent Docker storage when Cloudinary is blank; production requires Cloudinary.

7. To grant Platform Admin access to an already verified account only:

   ```powershell
   .\scripts\set-superadmin.ps1
   docker compose up -d --force-recreate api
   ```

   Sign out and back in, then open `http://127.0.0.1:3000/admin/`. Platform Admin authorization is separate from workspace owner/admin roles.

The `migrate` service applies every Alembic migration before the API, worker, and scheduler start. Before a clean rebuild you can run `.\scripts\verify-source-integrity.ps1`; `.\scripts\rebuild-clean.ps1` performs an integrity check and clean image rebuild without deleting local data. Use `-ResetData` only when you intentionally want to erase local Docker volumes.

## Development

Frontend:

```bash
npm ci --prefix frontend
npm run dev --prefix frontend
```

Backend requires Python 3.13 and `uv`:

```bash
cd backend
uv sync --all-groups
uv run pytest
```

## Documentation

- `docs/FEATURE_IMPLEMENTATION.md` — feature-to-code implementation map
- `docs/STRIPE_SETUP.md` — test/live Stripe products, Price IDs, environment, webhook events, portal, and acceptance checklist
- `docs/DEPLOYMENT_RUNBOOK.md` — production environment, providers, deployment, backup, and rollback
- `PRODUCTION_READINESS.md` — release validation evidence and go-live boundary

Never deploy the included local secrets. Generate production values and use a managed secret store.
