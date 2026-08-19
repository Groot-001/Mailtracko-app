from typing import Any

from fastapi import Request

from src.shared.exceptions.base_exceptions import UnAuthorizedError


class require_access:
    """FastAPI dependency guard that checks access conditions.

    Relies on request.state values set by middleware (SessionMiddleware).
    """

    def __init__(
        self,
        authenticated: bool = False,
        email_verified: bool = False,
    ):
        self._authenticated = authenticated
        self._email_verified = email_verified

    async def __call__(self, request: Request) -> Any:
        if self._authenticated:
            session_uuid = getattr(request.state, "session_uuid", None)
            user_id = getattr(request.state, "user_id", None)

            if not session_uuid:
                raise UnAuthorizedError(error="Not authenticated")

            if not user_id:
                raise UnAuthorizedError(error="Invalid session")

            user = getattr(request.state, "user", None)

            if self._email_verified:
                if not user or not user.is_email_verified():
                    raise UnAuthorizedError(error="Email not verified")

        return None
