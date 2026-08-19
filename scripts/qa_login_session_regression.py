#!/usr/bin/env python3
"""Static regression guard for the login -> login session loop."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(path: str, *needles: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"FAIL: {path} is missing expected login-session guards: {missing}")
    return text


axios = require(
    "frontend/src/shared/api/axios.ts",
    'const DEFAULT_API_BASE_URL = "/api/v1"',
    "browserIsLoopback && apiIsLoopback",
    "isPublicBrowserRoute()",
    "window.location.replace(loginUrl)",
)

login_hook = require(
    "frontend/src/feature/login/hooks/useLoginHooks.ts",
    "bootstrapApp({ authRetries: 2",
    "completePendingInvitation()",
    "MailTracko could not establish the browser session",
)
if login_hook.index("bootstrapApp({ authRetries: 2") > login_hook.index("completePendingInvitation()"):
    raise SystemExit("FAIL: pending invitation is attempted before the authenticated session is verified")

require(
    "frontend/src/feature/login/components/LoginForm.tsx",
    'getApiUrl("/auth/oauth/login/google")',
)
require(
    "frontend/src/feature/login/components/Register.tsx",
    'getApiUrl("/auth/oauth/login/google")',
)
require(
    "backend/src/core/utils/response.py",
    'urlparse(config.FRONTEND_URL).scheme.lower() == "https"',
)

if 'window.location.href = "/login"' in axios:
    raise SystemExit("FAIL: unconditional 401 hard redirect to /login reintroduced")

print("PASS: login session regression guards are present.")
