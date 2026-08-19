from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.utils.response import CustomResponse as cr
from src.modules.auth.auth_container import get_auth_container
from src.modules.auth.infrastructure.uow.auth_uow import AuthUOW
from src.modules.auth.presentation.schemas.auth_session_schemas import (
    RevokeSessionRequest,
)
from src.shared.dependencies.access_guard import require_access
from src.shared.infrastructure.db import get_async_session

router = APIRouter(prefix="/auth/sessions", tags=["Authentication - Session"])
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
auth = Depends(require_access(authenticated=True, email_verified=True))


@router.get("", dependencies=[auth])
async def list_sessions(request: Request, session: AsyncSessionDep):
    """List all active (non-revoked) sessions for the current user."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        sessions = await auth_container.list_sessions_usecase().execute(
            user_id=request.state.user_id,
        )
        return cr.success(data=[_session_to_dict(s) for s in sessions])


@router.get("/current", dependencies=[auth])
async def get_current_session(request: Request, session: AsyncSessionDep):
    """Get details of the current session."""
    async with AuthUOW(session):
        current = None
        session_uuid = request.state.session_uuid
        if session_uuid:
            auth_container = get_auth_container(session)
            current = await auth_container.get_current_session_usecase().execute(
                user_id=request.state.user_id,
                current_session_uuid=session_uuid,
            )
        return cr.success(data=_session_to_dict(current) if current else None)


@router.post("/revoke", dependencies=[auth])
async def revoke_session(
    request: Request, body: RevokeSessionRequest, session: AsyncSessionDep
):
    """Revoke a specific session by its UUID."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        await auth_container.revoke_session_usecase().execute(
            user_id=request.state.user_id,
            session_uuid=body.session_uuid,
        )
        return cr.success(data={"message": "Session revoked"})


@router.post("/revoke-all", dependencies=[auth])
async def revoke_all_sessions(request: Request, session: AsyncSessionDep):
    """Revoke all active sessions for the current user."""
    async with AuthUOW(session):
        auth_container = get_auth_container(session)
        await auth_container.revoke_all_sessions_usecase().execute(
            user_id=request.state.user_id,
        )
        return cr.success(data={"message": "All sessions revoked"})


@router.post("/revoke-others", dependencies=[auth])
async def revoke_other_sessions(request: Request, session: AsyncSessionDep):
    """Revoke all active sessions except the session making this request."""
    async with AuthUOW(session):
        current_session_uuid = request.state.session_uuid
        auth_container = get_auth_container(session)
        await auth_container.revoke_other_sessions_usecase().execute(
            user_id=request.state.user_id,
            current_session_uuid=current_session_uuid,
        )
        return cr.success(data={"message": "Other sessions revoked"})


def _session_to_dict(s) -> dict | None:
    """Convert a session entity to a serializable dictionary."""
    if not s:
        return None
    return {
        "uuid": s.uuid,
        "ip_address": s.ip_address,
        "user_agent": s.user_agent,
        "expires_at": s.expires_at.isoformat() if s.expires_at else None,
        "revoked_at": s.revoked_at.isoformat() if s.revoked_at else None,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }
