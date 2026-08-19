from src.shared.domain.repository.base_repository_interface import IBaseRepository

from src.modules.auth.domain.entities.user_session_entity import UserSessionEntity


class IUserSessionRepository(IBaseRepository[UserSessionEntity]):
    async def revoke_all_for_user(self, user_id: int) -> None:
        """Revoke all active sessions for a given user in a single batch update."""
        ...

    async def revoke_all_except(self, user_id: int, exclude_session_uuid: str) -> None:
        """Revoke all active sessions except the one with the given UUID."""
        ...
