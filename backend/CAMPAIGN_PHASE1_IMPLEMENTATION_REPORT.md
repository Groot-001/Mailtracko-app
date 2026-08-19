# MailTracko Campaign Phase 1 Backend Report

Date: 2026-07-30


## Senior continuation hardening (v2)

This continuation keeps the existing module structure and business flow, while completing the A/B test sample-to-winner lifecycle that a production campaign product requires.

New implementation:

- Deterministic A/B sample membership using SHA-256 and the campaign UUID as a salt.
- Non-sampled recipients now enter an explicit `holdout` state and are not delivered before a winner is selected.
- Both A and B content candidates are snapshotted before launch for every A/B recipient, so later template edits cannot alter holdout or continuation content.
- Winner selection releases all unsent sample/holdout recipients to the winner and marks them as continuation recipients, keeping winner metrics limited to the actual test sample.
- Campaign review blocks a configuration whose `minimum_sample_size` is larger than the deterministic eligible sample.
- A/B API responses now expose sampled, remaining holdout and released continuation recipient counts.
- Recipient API responses expose `ab_test_sampled` for later frontend progress and diagnostics.
- A test-only root `conftest.py` provides a deterministic non-secret Fernet key, so `python -m pytest` runs without local secret setup. Production encryption configuration is unchanged.

## Implemented scope

Backend-only implementation. No frontend code was added or modified.

Included:

- Campaign draft/create/update/list/detail/duplicate/archive flow.
- Explicit campaign lifecycle and validated transitions: draft, ready, scheduled, launching, running, paused, completed, cancelled, failed, archived.
- Pre-send review of sender, contact list, campaign type configuration, template availability, audience eligibility, duplicates, suppression state, sending window, timezone and unresolved recipient variables.
- Immediate launch and timezone-aware one-time scheduling.
- Sending days, sending windows, campaign batch limits and sender/campaign daily limits.
- Organization-scoped sender, template, contact-list, recipient and analytics access.
- Immutable audience snapshot through campaign recipient rows.
- Immutable message content snapshots created before scheduling/launch.
- Durable logical messages with a unique idempotency key for campaign + recipient + sequence step + A/B variant.
- Fail-closed handling for uncertain provider outcomes to prevent blind retries and duplicate sends.
- Manual reconciliation endpoint for uncertain sends.
- Pause, resume with revalidation, cancel/stop and recipient cancellation reasons.
- Suppression/unsubscribe checks during review, snapshot and immediately before sending.
- Append-only deduplicated recipient event processing for delivery, open, click, reply, bounce, unsubscribe, meeting and custom events.
- Basic campaign analytics and rates.

Phase 2 features intentionally included in this delivery:

- Multi-step email sequences with ordered email/delay steps.
- Stop on reply, unsubscribe, click, meeting or configured custom event.
- Retry-safe step processing and per-step duplicate prevention.
- A/B variants A and B with exactly 100% allocation.
- Stable SHA-256 recipient assignment.
- Test audience percentage, sample size, duration, winner metric, manual winner and automatic winner selection.
- Background evaluation of A/B winner eligibility after campaign delivery finishes.

Not included:

- Advanced conditional sequence branching.
- Full inbox UI/backend workflow.
- Warmup, domain management, billing, advanced analytics exports and other Phase 2 modules.
- Frontend implementation.

## Important reliability changes

1. A provider timeout or connection-reset outcome is recorded as `uncertain`, not immediately retried.
2. An uncertain send must be reconciled as `sent`, `failed` or `retry` before further processing.
3. Message content is snapshotted before launch, so later template edits do not silently change a scheduled campaign.
4. Sequence retries are reset after a successful step, preventing previous-step attempts from consuming the next step's retry allowance.
5. A/B automatic winner selection respects configured sample and duration rules and requires at least one sent message.
6. Campaign resume revalidates sender, audience and content configuration.
7. Cancelled recipients receive `campaign_cancelled` stop metadata and cannot be processed later.

## Frontend API contract

Base prefix: `/api/v1/campaigns`

- `POST /` — create a campaign draft.
- `GET /` — list campaigns.
- `GET /summary` — campaign summary counters.
- `GET /{campaign_uuid}` — campaign detail.
- `PATCH /{campaign_uuid}` — update an editable campaign.
- `POST /{campaign_uuid}/duplicate` — create a new draft copy.
- `PUT /{campaign_uuid}/sequence` — configure sequence steps and stop conditions.
- `GET /{campaign_uuid}/sequence` — retrieve sequence configuration.
- `POST /{campaign_uuid}/sequence/preview` — preview sequence timeline.
- `PUT /{campaign_uuid}/ab-test` — configure A/B variants and winner rules.
- `GET /{campaign_uuid}/ab-test` — retrieve A/B configuration/results.
- `POST /{campaign_uuid}/ab-test/winner` — select a winner manually or by metric.
- `POST /{campaign_uuid}/review` — validate the campaign before schedule/launch.
- `POST /{campaign_uuid}/schedule` — schedule a future launch.
- `POST /{campaign_uuid}/launch` — launch immediately.
- `POST /{campaign_uuid}/process` — controlled processing endpoint; production delivery should normally use the worker.
- `POST /{campaign_uuid}/pause` — pause new delivery work.
- `POST /{campaign_uuid}/resume` — revalidate and resume.
- `POST /{campaign_uuid}/cancel` — permanently stop unsent recipients.
- `DELETE /{campaign_uuid}` — archive an eligible campaign.
- `GET /{campaign_uuid}/recipients` — recipient progress and failures.
- `GET /{campaign_uuid}/analytics` — basic campaign analytics.
- `POST /{campaign_uuid}/recipients/{recipient_uuid}/events` — record a deduplicated provider/mailbox event.
- `POST /{campaign_uuid}/recipients/{recipient_uuid}/reconcile-send` — resolve an uncertain provider outcome.

### A/B continuation fields for frontend

`GET /{campaign_uuid}/ab-test` additionally returns:

- `sampled_recipient_count` — recipients whose outcomes contribute to winner selection.
- `holdout_recipient_count` — recipients waiting for a winner.
- `released_recipient_count` — continuation recipients released to the selected winner.

Recipient rows additionally return `ab_test_sampled`. A recipient with status `holdout` must be displayed as waiting for winner selection, not as queued or failed.

### Reconcile-send body

```json
{
  "outcome": "sent",
  "provider_message_id": "provider-message-id",
  "provider_thread_id": "optional-provider-thread-id"
}
```

Allowed outcomes: `sent`, `failed`, `retry`. `provider_message_id` is required for `sent`.

## Migration result

- Alembic head: `f7a8b9c0d1e2`.
- Campaign migration chain is linear: `e5f6a7b8c9d0 -> f6a7b8c9d0e1 -> f7a8b9c0d1e2`.
- The hardening migrations add sending windows, sequence stop fields, A/B rules, recipient stop/bounce/holdout fields, durable campaign messages, content snapshots, message events, suppressions and campaign state history.
- A live `alembic upgrade head` was not executed because this environment did not provide a PostgreSQL service.

## Verification completed

- `python -m compileall -q src migrations` — passed.
- Campaign tests — 20 passed.
- Full test suite — 192 passed, 53 existing warnings.
- `alembic heads` — one head, `f7a8b9c0d1e2`.
- Production Compose YAML parsed successfully with six services.

The API import/startup command could not be executed in this container because project runtime dependencies were not installed (`prometheus_fastapi_instrumentator` was the first missing package). The dependency is declared in `pyproject.toml`; install dependencies or build the Docker image before running the startup check.

Docker itself was not available in this execution environment, so the production image and Compose stack were prepared but not built here.

## Campaign files changed

Additional continuation files:

- `migrations/versions/f7a8b9c0d1e2_campaign_ab_test_holdout_continuation.py`
- `src/modules/campaign/domain/enums/recipient_status.py`
- `src/modules/campaign/domain/services/campaign_rules.py`
- `src/modules/campaign/domain/services/__init__.py`
- `src/modules/campaign/application/services/campaign_service.py`
- `src/modules/campaign/infrastructure/models/campaign_models.py`
- `src/modules/campaign/infrastructure/repositories/campaign_repository_impl.py`
- `src/modules/campaign/presentation/schemas/campaign_schemas.py`
- `tests/unit/campaign/test_campaign_domain.py`
- `tests/unit/campaign/test_campaign_schemas.py`


- `migrations/versions/f6a7b8c9d0e1_campaign_phase1_sequence_ab_hardening.py`
- `src/modules/campaign/application/services/campaign_service.py`
- `src/modules/campaign/domain/entities/campaign.py`
- `src/modules/campaign/domain/enums/recipient_status.py`
- `src/modules/campaign/domain/enums/stop_reason.py`
- `src/modules/campaign/domain/services/__init__.py`
- `src/modules/campaign/domain/services/campaign_rules.py`
- `src/modules/campaign/infrastructure/background_tasks/campaign_tasks.py`
- `src/modules/campaign/infrastructure/models/__init__.py`
- `src/modules/campaign/infrastructure/models/campaign_models.py`
- `src/modules/campaign/infrastructure/repositories/campaign_repository_impl.py`
- `src/modules/campaign/presentation/routers/campaign_routers.py`
- `src/modules/campaign/presentation/schemas/campaign_schemas.py`
- `tests/unit/campaign/test_campaign_domain.py`
- `tests/unit/campaign/test_campaign_schemas.py`

## Required non-Campaign changes

- `conftest.py` — test-only deterministic environment defaults so the full suite can be collected without a developer secret. Production runtime behavior is unchanged.

- `src/modules/organization/domain/services/organization_domain_service.py` — removed an invalid seed-script import from the domain layer. A nearby comment explains the integration fix. Organization business logic was not changed.
- Contacts unit tests — aligned stale test doubles/constructors with the current Contacts repository and use-case interfaces. Production Contacts logic was not changed.
- Email Template unit tests — corrected stale package imports and current use-case setup. Production Email Template logic was not changed.
- `Dockerfile` — changed dependency installation to the committed lock file and added the required Uvicorn factory flag. A nearby comment explains the deployment change.
- `.dockerignore` — prevents secrets, virtual environments, caches and local files from entering the production image.
- `docker/docker-compose.production.yml` — adds private PostgreSQL/Redis, migration, API, Campaign worker and Campaign scheduler services.
- `env/.example.production.env` — placeholder-only production environment contract.
- `pyproject.toml` and `uv.lock` — constrain the validated runtime to Python 3.13 so deployment does not resolve an untested Python 3.14 dependency split. A nearby comment explains the change.

## Local commands

```bash
uv sync --dev --frozen
cp env/.example.env env/.env.local
# Fill local placeholder values.
docker compose -f docker/docker-compose.base.yml up -d
uv run alembic upgrade head
uv run uvicorn src.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

Run workers in separate terminals:

```bash
uv run dramatiq src.modules.campaign.infrastructure.background_tasks.campaign_tasks
uv run python scripts/campaign/run_scheduler.py
```

Run checks:

```bash
uv run python -m compileall src migrations
uv run pytest tests/unit/campaign -v
uv run pytest -v
uv run alembic heads
uv run alembic history
```

## Production Docker commands

Create the real production environment file without committing it:

```bash
cp env/.example.production.env env/.env.production
```

Fill every placeholder, then run:

```bash
docker compose --env-file env/.env.production -f docker/docker-compose.production.yml build
docker compose --env-file env/.env.production -f docker/docker-compose.production.yml up -d
docker compose --env-file env/.env.production -f docker/docker-compose.production.yml ps
docker compose --env-file env/.env.production -f docker/docker-compose.production.yml logs -f api campaign_worker campaign_scheduler
```

PostgreSQL and Redis are not published to the host in the production Compose file.
