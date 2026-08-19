from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.utils.response import CustomResponse as cr
from src.modules.auth.auth_container import get_auth_container
from src.modules.auth.infrastructure.uow.auth_uow import AuthUOW
from src.modules.auth.presentation.schemas.auth_schemas import VerifyEmailRequest
from src.shared.dependencies.access_guard import require_access
from src.shared.infrastructure.db import get_async_session
from src.shared.infrastructure.rate_limiter.rate_limiter import rate_limit

router = APIRouter(prefix="/auth/email", tags=["Authentication - Email"])
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
auth = Depends(require_access(authenticated=True))


@router.post("/verify", dependencies=[auth, Depends(rate_limit(max_requests=5, window_seconds=300, key_prefix="verify_email"))])
async def verify_email(
    request: Request, body: VerifyEmailRequest, session: AsyncSessionDep
):
    """Verify the current user's email using a verification token."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        usecase = auth_container.verify_email_usecase()
        await usecase.execute(user_id=request.state.user_id, token=body.token)
        return cr.success(data={"message": "Email verified successfully"})


@router.post("/resend", dependencies=[auth, Depends(rate_limit(max_requests=3, window_seconds=300, key_prefix="resend_verification"))])
async def resend_verification(request: Request, session: AsyncSessionDep):
    """Resend the email verification link to the current user."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        usecase = auth_container.resend_verification_usecase()
        await usecase.execute(user_id=request.state.user_id)
        return cr.success(data={"message": "Verification email sent"})
