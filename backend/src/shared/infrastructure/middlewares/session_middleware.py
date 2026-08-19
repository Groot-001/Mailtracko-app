from datetime import UTC, datetime, timedelta

from fastapi import Request
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from src.shared.infrastructure.db import async_session as _async_session
from src.shared.infrastructure.logger import logger


class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts session_uuid from cookie, validates session, and sets request.state.

    Sets the following on request.state:
        - session_uuid: str | None
        - user_id: int | None
        - user: UserEntity | None
        - ip_address: str | None
    """

    async def dispatch(self, request: Request, call_next):
        request.state.session_uuid = None
        request.state.user_id = None
        request.state.user = None
        request.state.ip_address = request.client.host if request.client else None
        request.state.user_agent = request.headers.get("user-agent")

        session_uuid = request.cookies.get("session_uuid")
        if session_uuid:
            request.state.session_uuid = session_uuid
            try:
                async with _async_session() as db_session:
                    from src.modules.auth.infrastructure.repositories.user_session_repository_impl import (
                        UserSessionRepository,
                    )
                    from src.modules.auth.infrastructure.repositories.user_repository_impl import (
                        UserRepository,
                    )

                    session_repo = UserSessionRepository(db_session)
                    user_session = await session_repo.get_by(uuid=session_uuid)
                    if user_session and not user_session.is_revoked() and not user_session.is_expired():
                        user_repo = UserRepository(db_session)
                        user = await user_repo.get_by_id(user_session.user_id)
                        # Session validity is not enough: suspension/deletion must
                        # take effect immediately for already-open browser sessions.
                        if user is not None and user.is_active and not user.is_deleted():
                            request.state.user_id = user_session.user_id
                            request.state.user = user

                            # Presence heartbeat: record meaningful authenticated activity
                            # at most once per minute to avoid a database write per request.
                            last_active_at = user_session.updated_at or user_session.created_at
                            now = datetime.now(UTC)
                            if last_active_at is None or now - last_active_at > timedelta(seconds=60):
                                await db_session.execute(
                                    text(
                                        "UPDATE sys_auth_user_sessions SET updated_at = :now "
                                        "WHERE id = :session_id AND revoked_at IS NULL"
                                    ),
                                    {"now": now, "session_id": user_session.id},
                                )
                                await db_session.commit()

                            logger.info(
                                "[SessionMiddleware] User loaded: id=%s, email_verified=%s, email_verified_at=%s",
                                user.id,
                                user.is_email_verified(),
                                user.email_verified_at.isoformat() if user.email_verified_at else None,
                            )
                        elif user is not None:
                            logger.warning(
                                "[SessionMiddleware] Rejected inactive/deleted user session: user_id=%s",
                                user_session.user_id,
                            )
            except Exception as e:
                logger.error("[SessionMiddleware] Error loading session: %s", str(e))

        response = await call_next(request)
        return response
