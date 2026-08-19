from src.modules.auth.domain.entities.user_session_entity import UserSessionEntity
from src.modules.auth.domain.services.user_session_domain_service import UserSessionDomainService
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class ListSessionsUseCase:
    def __init__(self, user_session_domain_service: UserSessionDomainService):
        self.user_session_domain_service = user_session_domain_service

    async def execute(self, user_id: int) -> list[UserSessionEntity]:
        try:
            return await self.user_session_domain_service.list_sessions_by_user_id(user_id)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to list sessions", internal_details=str(e)) from e


class GetCurrentSessionUseCase:
    def __init__(self, user_session_domain_service: UserSessionDomainService):
        self.user_session_domain_service = user_session_domain_service

    async def execute(self, user_id: int, current_session_uuid: str) -> UserSessionEntity | None:
        try:
            session = await self.user_session_domain_service.get_user_session_by_uuid(current_session_uuid)
            if session and session.user_id == user_id:
                return session
            return None
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to get current session", internal_details=str(e)) from e
