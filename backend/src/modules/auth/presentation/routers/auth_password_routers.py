from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.utils.response import CustomResponse as cr
from src.modules.auth.auth_container import get_auth_container
from src.modules.auth.infrastructure.uow.auth_uow import AuthUOW
from src.modules.auth.presentation.schemas.auth_schemas import (
    ForgotPasswordCodeVerifyRequest,
    ForgotPasswordRequest,
    ForgotPasswordResetRequest,
)
from src.shared.infrastructure.db import get_async_session
from src.shared.infrastructure.rate_limiter.rate_limiter import rate_limit

router = APIRouter(prefix="/auth/password", tags=["Authentication - Password"])
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]


@router.post("/forgot", dependencies=[Depends(rate_limit(max_requests=3, window_seconds=300, key_prefix="forgot_password"))])
async def forgot_password(body: ForgotPasswordRequest, session: AsyncSessionDep):
    """Send a six-digit password-reset security code."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        result = await auth_container.forgot_password_usecase().execute(email=body.email)
        return cr.success(data=result)


@router.post(
    "/forgot/verify-code",
    dependencies=[Depends(rate_limit(max_requests=5, window_seconds=300, key_prefix="forgot_password_verify"))],
)
async def verify_forgot_password_code(
    body: ForgotPasswordCodeVerifyRequest, session: AsyncSessionDep
):
    """Verify the OTP and issue a short-lived, one-time reset challenge."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        result = await auth_container.verify_forgot_password_usecase().verify_code(
            token=body.token
        )
        return cr.success(data=result, message="Verification code accepted")


@router.post(
    "/forgot/reset",
    dependencies=[Depends(rate_limit(max_requests=5, window_seconds=300, key_prefix="forgot_password_reset"))],
)
async def reset_forgotten_password(
    body: ForgotPasswordResetRequest, session: AsyncSessionDep
):
    """Create a new password using the server-issued reset challenge."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        result = await auth_container.verify_forgot_password_usecase().reset_with_challenge(
            reset_challenge=body.reset_challenge,
            new_password=body.new_password,
        )
        return cr.success(data=result, message="Password reset successfully")
