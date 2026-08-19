from typing import Annotated
from urllib.parse import urlencode, urlsplit

from fastapi import APIRouter, Depends, Query, status
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from src.core.config.settings import config
from src.core.utils.response import get_cookie_response
from src.modules.auth.auth_container import get_auth_container
from src.modules.auth.infrastructure.uow.auth_uow import AuthUOW
from src.shared.exceptions.base_exceptions import DomainError, InvalidError
from src.shared.infrastructure.db import get_async_session
from src.shared.infrastructure.logger import logger
from src.shared.infrastructure.rate_limiter.rate_limiter import rate_limit

router = APIRouter(prefix="/auth/oauth", tags=["Authentication - OAuth"])
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


def _google_callback_origin() -> str:
    """Return the browser origin that owns Google's callback URL.

    The OAuth response sets a host-only session cookie. Redirecting to a
    different hostname immediately afterwards (for example localhost ->
    127.0.0.1) makes the browser correctly withhold that cookie and looks like
    a failed login. Keep the post-OAuth navigation on the exact callback
    origin so the cookie remains available to MailTracko.
    """

    parsed = urlsplit(config.GOOGLE_REDIRECT_URI)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return config.FRONTEND_URL.rstrip("/")


def _oauth_cookie_secure() -> bool:
    """Secure cookies only when the browser-facing OAuth callback uses HTTPS."""

    return urlsplit(_google_callback_origin()).scheme == "https"


@router.get("/login/{provider}")
async def oauth_login(
    provider: str,
    request: Request,
    session: AsyncSessionDep,
):
    """Redirect the user to the supported OAuth provider."""
    if provider != "google":
        raise InvalidError(error="Unsupported OAuth provider")
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        redirect_url = await auth_container.oauth_login_usecase().execute(provider=provider)
        return RedirectResponse(url=redirect_url)


@router.get(
    "/callback/{provider}",
    dependencies=[
        Depends(
            rate_limit(
                max_requests=5,
                window_seconds=300,
                key_prefix="oauth_callback",
            )
        )
    ],
)
async def oauth_callback(
    provider: str,
    request: Request,
    session: AsyncSessionDep,
    code: str | None = Query(default=None),
    state: str = Query(default=""),
    error: str | None = Query(default=None),
):
    """Handle Google OAuth, create the MailTracko session, then redirect directly."""
    if provider != "google":
        raise InvalidError(error="Unsupported OAuth provider")

    frontend_origin = _google_callback_origin()
    secure_cookie = _oauth_cookie_secure()

    if error:
        logger.warning("[OAuth] Provider returned error: %s", error)
        return RedirectResponse(url=f"{frontend_origin}/login?error=oauth_denied")
    if not code or not state:
        return RedirectResponse(
            url=f"{frontend_origin}/login?error=oauth_invalid_callback"
        )

    try:
        async with AuthUOW(session):
            auth_container = get_auth_container(session)
            user = await auth_container.oauth_callback_usecase().execute(
                provider=provider,
                code=code,
                state=state,
            )
            payload = await auth_container.login_user_usecase().oauth_login(
                user=user,
                ip_address=request.state.ip_address,
                user_agent=request.state.user_agent,
            )
    except DomainError as exc:
        logger.warning("[OAuth] Callback rejected: %s", exc.error)
        query = urlencode({"error": "oauth_callback_failed", "message": exc.error})
        return RedirectResponse(
            url=f"{frontend_origin}/login?{query}",
            status_code=status.HTTP_302_FOUND,
        )

    if payload.get("requires_2fa"):
        response = RedirectResponse(
            url=f"{frontend_origin}/verify-2fa",
            status_code=status.HTTP_302_FOUND,
        )
        return get_cookie_response(
            cookies={
                "mfa_challenge": {
                    "value": payload["temp_token"],
                    "max_age": 300,
                    "httponly": True,
                    "samesite": "lax",
                    "secure": secure_cookie,
                }
            },
            response=response,
        )

    response = RedirectResponse(
        url=f"{frontend_origin}/dashboard",
        status_code=status.HTTP_302_FOUND,
    )
    return get_cookie_response(
        cookies={
            "session_uuid": {
                "value": payload["session_uuid"],
                "httponly": True,
                "samesite": "lax",
                "secure": secure_cookie,
            }
        },
        response=response,
    )
