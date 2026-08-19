from src.modules.auth.domain.entities.user_session_entity import UserSessionEntity
from src.modules.auth.domain.repositories.user_session_repository import IUserSessionRepository
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class UserSessionDomainService:
    """Domain service for user session entity operations."""

    def __init__(self, repository: IUserSessionRepository):
        self.repository = repository

    async def create_user_session(self, session_entity: UserSessionEntity) -> UserSessionEntity:
        """Persist a new user session."""
        try:
            return await self.repository.add(session_entity)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to create session", internal_details=str(e)) from e

    async def get_user_session_by_uuid(self, session_uuid: str) -> UserSessionEntity | None:
        """Retrieve a session by its UUID."""
        try:
            return await self.repository.get_by(uuid=session_uuid)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve session", internal_details=str(e)) from e

    async def update_user_session(self, session_entity: UserSessionEntity) -> UserSessionEntity:
        """Persist changes to an existing session."""
        try:
            return await self.repository.update(session_entity)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to update session", internal_details=str(e)) from e

    async def list_sessions_by_user_id(self, user_id: int) -> list[UserSessionEntity]:
        """Retrieve all active (non-revoked) sessions for a given user."""
        try:
            return await self.repository.filter(user_id=user_id, revoked_at=None)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to list sessions", internal_details=str(e)) from e

    async def revoke_all_sessions_for_user(self, user_id: int) -> list[UserSessionEntity]:
        """Revoke all active sessions for a user and return the revoked sessions."""
        try:
            sessions = await self.repository.filter(user_id=user_id, revoked_at=None)
            if not sessions:
                return []
            await self.repository.revoke_all_for_user(user_id)
            for session in sessions:
                session.revoke()
            return sessions
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to revoke sessions", internal_details=str(e)) from e

    async def revoke_all_except_current(self, user_id: int, current_session_uuid: str) -> None:
        """Revoke all active sessions except the current one."""
        try:
            await self.repository.revoke_all_except(user_id, current_session_uuid)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to revoke other sessions", internal_details=str(e)) from e
