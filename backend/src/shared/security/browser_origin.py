from __future__ import annotations

from urllib.parse import urlparse

from fastapi import Request

from src.core.config.settings import config

_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def normalize_origin(value: str | None) -> str | None:
    """Return a canonical http(s) origin, or ``None`` for malformed input."""
    if not value:
        return None

    try:
        parsed = urlparse(value.strip())
    except ValueError:
        return None

    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None

    host = parsed.hostname.lower()
    try:
        port = parsed.port
    except ValueError:
        return None

    default_port = 80 if parsed.scheme.lower() == "http" else 443
    port_suffix = f":{port}" if port and port != default_port else ""
    display_host = f"[{host}]" if ":" in host else host
    return f"{parsed.scheme.lower()}://{display_host}{port_suffix}"


def _trusted_origins() -> set[str]:
    values = [config.FRONTEND_URL, *config.CORS_ALLOWED_ORIGINS]
    return {origin for value in values if (origin := normalize_origin(value))}


def is_trusted_frontend_origin(origin: str | None) -> bool:
    normalized = normalize_origin(origin)
    if not normalized:
        return False

    if normalized in _trusted_origins():
        return True

    parsed = urlparse(normalized)
    is_loopback_origin = (parsed.hostname or "").lower() in _LOOPBACK_HOSTS

    # Local development often flips between localhost and 127.0.0.1. Some
    # deployments also launch the backend with ENVIRONMENT=production while
    # temporarily using a loopback Google callback for local verification. In
    # that case the configured GOOGLE_REDIRECT_URI itself is the explicit
    # signal that loopback OAuth is intended. A real production callback on
    # app.mailtracko.com never enables this exception.
    try:
        google_callback_host = (urlparse(config.GOOGLE_REDIRECT_URI).hostname or "").lower()
    except ValueError:
        google_callback_host = ""

    if is_loopback_origin and (
        not config.is_production or google_callback_host in _LOOPBACK_HOSTS
    ):
        return True

    return False


def resolve_frontend_origin(request: Request) -> str:
    """Resolve the browser origin that initiated an auth flow.

    OAuth login is a top-level navigation through the frontend's /api proxy.
    The browser Referer/Origin therefore gives us the exact localhost-vs-
    127.0.0.1 host the user is actually on. We keep the value only when it is a
    configured origin (or a loopback origin in non-production environments).
    """
    candidates: list[str | None] = [
        request.headers.get("origin"),
        request.headers.get("referer"),
    ]

    forwarded_host = request.headers.get("x-forwarded-host")
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_host:
        proto = (forwarded_proto or request.url.scheme or "http").split(",", 1)[0].strip()
        host = forwarded_host.split(",", 1)[0].strip()
        candidates.append(f"{proto}://{host}")

    candidates.append(str(request.base_url))
    candidates.append(config.FRONTEND_URL)

    for candidate in candidates:
        normalized = normalize_origin(candidate)
        if normalized and is_trusted_frontend_origin(normalized):
            return normalized

    # FRONTEND_URL is validated in production and is the safest final fallback.
    return normalize_origin(config.FRONTEND_URL) or config.FRONTEND_URL.rstrip("/")


def frontend_origin_from_state(value: object | None) -> str:
    candidate = value if isinstance(value, str) else None
    if is_trusted_frontend_origin(candidate):
        return normalize_origin(candidate) or config.FRONTEND_URL.rstrip("/")
    return normalize_origin(config.FRONTEND_URL) or config.FRONTEND_URL.rstrip("/")


def cookie_secure_for_origin(origin: str) -> bool:
    normalized = normalize_origin(origin)
    return bool(normalized and normalized.startswith("https://"))


def cookie_secure_for_request(request: Request) -> bool:
    """Choose Secure based on the browser-facing request, not a stale env host."""
    return cookie_secure_for_origin(resolve_frontend_origin(request))
