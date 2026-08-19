from src.modules.auth.domain.events.auth_session_domain_events import UserSessionUpdatedEvent
from src.modules.auth.domain.services.user_session_domain_service import UserSessionDomainService
from src.shared.exceptions.base_exceptions import DomainError, ForbiddenError, InvalidError, ServerError
from src.shared.mediator.mediator import mediator


class RevokeSessionUseCase:
    def __init__(self, user_session_domain_service: UserSessionDomainService):
        self.user_session_domain_service = user_session_domain_service

    async def execute(self, user_id: int, session_uuid: str) -> None:
        try:
            session = await self.user_session_domain_service.get_user_session_by_uuid(session_uuid)
            if not session:
                raise InvalidError(error="Session not found")

            if session.user_id != user_id:
                raise ForbiddenError(error="You do not have permission to revoke this session")

            if session.is_revoked() or session.is_expired():
                raise InvalidError(error="Session not found")

            session.revoke()
            await self.user_session_domain_service.update_user_session(session)

            session.add_event(
                UserSessionUpdatedEvent(session_uuid=session_uuid, value="revoked")
            )
            for event in session.pull_events():
                await mediator.publish(event)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to revoke session", internal_details=str(e)) from e


class RevokeAllSessionsUseCase:
    def __init__(self, user_session_domain_service: UserSessionDomainService):
        self.user_session_domain_service = user_session_domain_service

    async def execute(self, user_id: int) -> None:
        try:
            sessions = await self.user_session_domain_service.revoke_all_sessions_for_user(user_id)
            for session in sessions:
                session.add_event(
                    UserSessionUpdatedEvent(session_uuid=session.uuid, value="revoked")
                )
                for event in session.pull_events():
                    await mediator.publish(event)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to revoke all sessions", internal_details=str(e)) from e
