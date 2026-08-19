from src.modules.auth.domain.events.auth_session_domain_events import UserSessionUpdatedEvent
from src.modules.auth.domain.services.user_session_domain_service import UserSessionDomainService
from src.shared.exceptions.base_exceptions import DomainError, ServerError, UnAuthorizedError
from src.shared.mediator.mediator import mediator


class LogoutUserUseCase:
    def __init__(self, user_session_domain_service: UserSessionDomainService):
        self.user_session_domain_service = user_session_domain_service

    async def execute(self, session_uuid: str | None = None, user_id: int | None = None) -> None:
        try:
            if not session_uuid:
                raise UnAuthorizedError(error="Session UUID is required for logging out")

            session = await self.user_session_domain_service.get_user_session_by_uuid(session_uuid)
            if not session or session.is_expired() or session.is_revoked():
                raise UnAuthorizedError(error="Invalid session")

            if session.user_id != user_id:
                raise UnAuthorizedError(error="Session does not belong to this user")

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
            raise ServerError(error="An error occurred while logging out", internal_details=str(e)) from e
