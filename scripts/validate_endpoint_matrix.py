#!/usr/bin/env python3
"""Statically verify that every frontend Axios call has a backend route/method."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "src"
BACKEND = ROOT / "backend" / "src" / "modules"


def canonical(path: str) -> str:
    path = re.sub(r"\$\{[^}]+\}", "{}", path)
    path = re.sub(r"\{[^}:]+(?::[^}]+)?\}", "{}", path)
    path = re.sub(r"/+", "/", path.strip())
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1:
        path = path.rstrip("/")
    return path


def frontend_calls() -> list[tuple[str, str, Path]]:
    calls: list[tuple[str, str, Path]] = []
    call_re = re.compile(r"api\.(get|post|put|patch|delete)(?:\s*<.*?>)?\s*\(", re.S)
    for file in sorted(FRONTEND.rglob("*.ts")) + sorted(FRONTEND.rglob("*.tsx")):
        source = file.read_text(encoding="utf-8")
        for match in call_re.finditer(source):
            tail = source[match.end():]
            string_match = re.match(r"\s*([`\"'])(.*?)\1", tail, re.S)
            if not string_match:
                continue
            calls.append((match.group(1).upper(), canonical(string_match.group(2)), file))
    return calls


route_files: list[tuple[Path, str]] = [
    (BACKEND / "auth/presentation/routers/auth_core_routers.py", "/auth"),
    (BACKEND / "auth/presentation/routers/auth_email_routers.py", "/auth/email"),
    (BACKEND / "auth/presentation/routers/auth_oauth_routers.py", "/auth/oauth"),
    (BACKEND / "auth/presentation/routers/auth_password_routers.py", "/auth/password"),
    (BACKEND / "auth/presentation/routers/auth_session_routers.py", "/auth/sessions"),
    (BACKEND / "organization/presentation/routers/organization_routers.py", "/organizations"),
    (BACKEND / "email_account/presentation/routers/email_account_routers.py", "/email-accounts"),
    (BACKEND / "contacts/presentation/routers/contact_list_routers.py", "/contact-lists"),
    (BACKEND / "contacts/presentation/routers/sheets_routers.py", "/contact-lists"),
    (BACKEND / "email_template/presentation/routers/email_template_routers.py", ""),
    (BACKEND / "campaign/presentation/routers/campaign_routers.py", "/campaigns"),
    (BACKEND / "platform/presentation/workspace_routers.py", "/platform"),
    (BACKEND / "platform/presentation/billing_routers.py", "/billing"),
    (BACKEND / "platform/presentation/support_routers.py", "/support"),
    (BACKEND / "platform/presentation/admin_routers.py", "/admin"),
]

backend_routes: set[tuple[str, str]] = set()
decorator_re = re.compile(
    r"@(?:router|public_router|protected_router|private_router|logout_router)\."
    r"(get|post|put|patch|delete)\(\s*[\"']([^\"']*)[\"']",
    re.S,
)
for file, prefix in route_files:
    source = file.read_text(encoding="utf-8")
    for method, route in decorator_re.findall(source):
        backend_routes.add((method.upper(), canonical(prefix + route)))

missing: list[str] = []
calls = frontend_calls()
for method, route, file in calls:
    if (method, route) not in backend_routes:
        missing.append(f"{method} {route} from {file.relative_to(ROOT)}")

if missing:
    print("Frontend/backend endpoint matrix failed:")
    for item in missing:
        print(f" - {item}")
    sys.exit(1)

print(
    f"Frontend/backend endpoint matrix passed: {len(calls)} Axios calls matched "
    f"against {len(backend_routes)} backend routes."
)
