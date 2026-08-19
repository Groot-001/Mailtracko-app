from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.user_entity import UserEntity
from src.modules.auth.infrastructure.repositories.user_repository_impl import (
    UserRepository,
)
from src.modules.auth.infrastructure.repositories.user_session_repository_impl import (
    UserSessionRepository,
)
from src.shared.exceptions.base_exceptions import UnAuthorizedError
from src.shared.infrastructure.db import get_async_session
from src.shared.infrastructure.token.token_service import TokenService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session),
) -> UserEntity:
    token_service = TokenService()
    payload = token_service.validate_token(credentials.credentials)

    user_uuid = payload.get("sub")
    if not user_uuid:
        raise UnAuthorizedError("Invalid token payload")

    session_uuid = payload.get("sid")
    if session_uuid:
        session_repo = UserSessionRepository(session)
        user_session = await session_repo.get_by(uuid=session_uuid)
        if not user_session:
            raise UnAuthorizedError("Session not found")
        if user_session.is_revoked():
            raise UnAuthorizedError("Session has been revoked")
        if user_session.is_expired():
            raise UnAuthorizedError("Session has expired")

    user_repo = UserRepository(session)
    user = await user_repo.get_by(uuid=user_uuid)
    if not user:
        raise UnAuthorizedError("User not found")

    if not user.is_active:
        raise UnAuthorizedError("Account is deactivated")

    return user
