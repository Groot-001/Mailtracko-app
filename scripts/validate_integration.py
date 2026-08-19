#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"

errors: list[str] = []
checks = 0


def require(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        errors.append(message)


def text(path: Path) -> str:
    require(path.exists(), f"Missing file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8") if path.exists() else ""


# Relative TypeScript imports.
for source in (FRONTEND / "src").rglob("*"):
    if source.suffix not in {".ts", ".tsx"}:
        continue
    content = source.read_text(encoding="utf-8")
    for specifier in re.findall(r'(?:from\s+|import\s*\()\s*["\']([^"\']+)["\']', content):
        if not specifier.startswith("."):
            continue
        base = (source.parent / specifier).resolve()
        candidates = (
            base,
            Path(f"{base}.ts"),
            Path(f"{base}.tsx"),
            base / "index.ts",
            base / "index.tsx",
        )
        require(any(candidate.exists() for candidate in candidates), f"Missing relative import {specifier} in {source.relative_to(FRONTEND)}")

# Case-insensitive filename collisions (Windows safety).
seen: dict[str, Path] = {}
for path in ROOT.rglob("*"):
    if not path.is_file() or any(part in {".git", "node_modules", ".venv", "venv"} for part in path.parts):
        continue
    key = str(path.relative_to(ROOT)).casefold()
    require(key not in seen, f"Case-insensitive filename collision: {seen.get(key)} and {path}")
    seen[key] = path

campaign_api = text(FRONTEND / "src/feature/campaigns/api/campaignApi.ts")
campaign_types = text(FRONTEND / "src/feature/campaigns/types/campaign.types.ts")
campaign_router = text(BACKEND / "src/modules/campaign/presentation/routers/campaign_routers.py")
campaign_schemas = text(BACKEND / "src/modules/campaign/presentation/schemas/campaign_schemas.py")

for endpoint in (
    "/campaigns",
    "/sequence",
    "/sequence/preview",
    "/ab-test",
    "/ab-test/winner",
    "/review",
    "/schedule",
    "/launch",
    "/pause",
    "/resume",
    "/cancel",
    "/recipients",
    "/analytics",
):
    require(endpoint in campaign_api, f"Frontend campaign API is missing {endpoint}")

for field in (
    "stop_on_click",
    "stop_on_meeting",
    "custom_stop_events",
    "minimum_sample_size",
    "test_duration_hours",
    "sampled_recipient_count",
    "holdout_recipient_count",
    "released_recipient_count",
    "sending_window_start",
    "sending_window_end",
    "sending_days",
    "ab_test_sampled",
    "delivery_rate",
    "reply_rate",
):
    require(field in campaign_types, f"Frontend campaign contract is missing field {field}")
    require(field in campaign_schemas, f"Backend campaign schema is missing field {field}")

for route in (
    '/{campaign_uuid}/sequence/preview',
    '/{campaign_uuid}/analytics',
    '/{campaign_uuid}/ab-test',
):
    require(route in campaign_router, f"Backend campaign router is missing {route}")

template_router = text(BACKEND / "src/modules/email_template/presentation/routers/email_template_routers.py")
template_types = text(FRONTEND / "src/feature/templates/types/template.types.ts")
require(template_router.count("TemplateDetailResponseSchema") >= 3, "Template detail endpoints are not using the body_html detail schema")
require("body_html: string" in template_types, "Frontend template detail body_html must be required")

organization_router = text(BACKEND / "src/modules/organization/presentation/routers/organization_routers.py")
auth_router = text(BACKEND / "src/modules/auth/presentation/routers/auth_core_routers.py")
register_api = text(FRONTEND / "src/feature/login/api/registerApi.ts")
require('/invitations/validate' in organization_router, "Backend public invitation validation endpoint is missing")
require('/invitations/public/decline' in organization_router, "Backend public invitation decline endpoint is missing")
require('if body.invite_token:' in auth_router, "Signup does not accept an invitation transactionally")
require('/organizations/invitations/validate' in register_api, "Frontend invitation validation path is not integrated")
require('/organizations/invitations/public/decline' in register_api, "Frontend invitation decline path is not integrated")
require('/organizations/invitations/accept' in register_api, "Frontend invitation acceptance path is not integrated")
pending_invitation = text(FRONTEND / "src/shared/auth/pendingInvitation.ts")
initial_route = text(FRONTEND / "src/shared/app/resolveInitialRoute.ts")
require("completePendingInvitation" in pending_invitation, "Existing-user invitation completion helper is missing")
require('return "/pending-invitation"' in initial_route, "Pending invitations still resolve to a missing route")
require("/invitations/${" not in initial_route, "Stale non-existent invitation route remains")

route_tree = text(FRONTEND / "src/routeTree.gen.ts")
require("/organization/notifications" in route_tree, "Plural organization notifications route is missing")
require("/pending-invitation" in route_tree, "Protected pending invitation route is missing")
require("/organization/notification'" not in route_tree, "Stale singular organization notification route remains")

vite_config = text(FRONTEND / "vite.config.ts")
require("192.168." not in vite_config, "Vite config still contains a private LAN backend address")
require("VITE_API_PROXY_TARGET" in vite_config, "Vite API proxy is not configurable")

# Core frontend API paths must have matching backend route families.
auth_api_text = "\n".join(
    text(path)
    for path in (
        FRONTEND / "src/feature/login/api/loginApi.ts",
        FRONTEND / "src/feature/login/api/registerApi.ts",
        FRONTEND / "src/feature/login/api/verifyEmailApi.ts",
        FRONTEND / "src/feature/login/api/forgotPasswordApi.ts",
        FRONTEND / "src/shared/api/authApi.ts",
    )
)
auth_backend_text = "\n".join(
    text(path)
    for path in (BACKEND / "src/modules/auth/presentation/routers").glob("*_routers.py")
)
for endpoint in (
    "/auth/signup", "/auth/login", "/auth/me", "/auth/profile",
    "/auth/profile/image", "/auth/password/change", "/auth/password/forgot",
    "/auth/password/forgot/verify", "/auth/email/verify", "/auth/email/resend",
    "/auth/2fa/setup", "/auth/2fa/verify", "/auth/2fa/disable",
    "/auth/2fa/verify-login",
):
    require(endpoint in auth_api_text, f"Frontend auth API is missing {endpoint}")

workspace_api = text(FRONTEND / "src/shared/api/workspaceApi.ts")
email_router = text(BACKEND / "src/modules/email_account/presentation/routers/email_account_routers.py")
contact_router = text(BACKEND / "src/modules/contacts/presentation/routers/contact_list_routers.py")
require('"/email-accounts/"' in workspace_api and '@protected_router.get("/"' in email_router, "Email account list contract is missing")
require('"/contact-lists/"' in workspace_api and '@private_router.get("/"' in contact_router, "Contact list contract is missing")
require('/contacts`' in workspace_api and '/contacts"' in contact_router, "Contact-list count contract is missing")

new_modules = "\n".join(
    path.read_text(encoding="utf-8")
    for directory in (FRONTEND / "src/feature/templates", FRONTEND / "src/feature/campaigns")
    for path in directory.rglob("*")
    if path.suffix in {".ts", ".tsx", ".css"}
).lower()
for forbidden in ("purple", "violet", "indigo"):
    require(forbidden not in new_modules, f"Forbidden old theme token remains: {forbidden}")


# Session security and local runtime integration.
axios_api = text(FRONTEND / "src/shared/api/axios.ts")
frontend_source = "\n".join(
    path.read_text(encoding="utf-8")
    for path in (FRONTEND / "src").rglob("*")
    if path.suffix in {".ts", ".tsx"}
)
response_helpers = text(BACKEND / "src/core/utils/response.py")
smtp_adapter = text(
    BACKEND
    / "src/shared/infrastructure/notification/adapter/email/email_notification.py"
)
require("withCredentials: true" in axios_api, "Axios must send the backend session cookie")
require("document.cookie" not in frontend_source, "Frontend must not expose the session UUID through document.cookie")
require("Authorization = `Bearer" not in axios_api, "Session UUID must not be copied into an Authorization header")
require("config.is_production or config.is_staging" in response_helpers, "Cookie Secure default is not environment-aware")
require("config.SMTP_REQUIRE_AUTH" in smtp_adapter, "Real SMTP authentication guard is missing")
require("SMTP_MAX_RETRIES" in smtp_adapter and "for attempt in range" in smtp_adapter, "Bounded SMTP retry logic is missing")
require("mailpit" in smtp_adapter and "127.0.0.1" in smtp_adapter, "Real SMTP adapter must reject local Mailpit/loopback hosts")

# Senior stabilization contracts: protect the runtime fixes that previously
# failed only after Docker/browser execution.
configure_local_ps = text(ROOT / "scripts/configure-local.ps1")
configure_local_sh = text(ROOT / "scripts/configure-local.sh")
alembic_env = text(BACKEND / "migrations/env.py")
cloudinary_uploader = text(BACKEND / "src/shared/infrastructure/storage/cloudinary_uploader.py")
image_validation = text(BACKEND / "src/shared/infrastructure/storage/image_validation.py")
platform_access = text(BACKEND / "src/modules/platform/presentation/workspace_routers.py")
platform_admin = text(BACKEND / "src/modules/platform/presentation/admin_routers.py")
session_middleware = text(BACKEND / "src/shared/infrastructure/middlewares/session_middleware.py")
email_notification = smtp_adapter
email_dashboard = text(FRONTEND / "src/feature/email-accounts/components/EmailAccountsDashboard.tsx")
product_shell = text(FRONTEND / "src/shared/components/ProductShell.tsx")

require('headers:' not in axios_api or '"Content-Type": "application/json"' not in axios_api, "Axios must not globally force JSON Content-Type because it breaks FormData boundaries")
require("EscapeDataString" in configure_local_ps, "PowerShell setup must URL-encode the database password")
require('quote(db, safe="")' in configure_local_sh, "Shell setup must URL-encode the database password")
require("New-FernetKey" in configure_local_ps and "SECRET_ENCRYPTION_KEY" in configure_local_ps, "PowerShell setup must generate a valid Fernet encryption key")
require('DATABASE_URL.replace("%", "%%")' in alembic_env, "Alembic must escape percent signs in URL-encoded database credentials")
require("_upload_local_files" in cloudinary_uploader and 'config.ENVIRONMENT.value == "production"' in cloudinary_uploader, "Local development upload fallback / production storage guard is missing")
require("validate_image_upload" in image_validation and "_validate_svg" in image_validation, "Server-side image signature and safe SVG validation is missing")
require("if not is_platform_admin" in platform_access and '"organization_uuid": context.organization.uuid if context is not None else None' in platform_access, "Dedicated platform admins must be allowed without a workspace")
require("UserSessionModel.revoked_at.is_(None)" in platform_admin and "admin.user_status_changed" in platform_admin, "Admin user suspension must revoke active sessions")
require("user.is_active and not user.is_deleted()" in session_middleware, "Session middleware must reject suspended/deleted users")
require("add_related(" in email_notification and "cid:" in email_notification and 'cid=f"<{cid}>"' in email_notification, "Transactional email branding must use embedded CID assets")
require("Date.now() + 10 * 60 * 1000" in email_dashboard, "Gmail OAuth popup polling must have a hard timeout")
require("Warmup unavailable" in email_dashboard and "~120 emails" not in email_dashboard, "Sender Accounts must not present fake warmup activity or controls")
require("Boolean(platformAccess.data?.organization_uuid)" in product_shell, "Platform-only admins must not be treated as if they have a customer workspace")

require((ROOT / "docker-compose.yml").exists(), "Integrated Docker Compose file is missing")
require((FRONTEND / "Dockerfile").exists(), "Frontend Dockerfile is missing")
require((FRONTEND / "nginx.conf").exists(), "Frontend nginx proxy configuration is missing")

if errors:
    print("Integration validation failed:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print(f"Integration contract validation passed: {checks} checks.")
