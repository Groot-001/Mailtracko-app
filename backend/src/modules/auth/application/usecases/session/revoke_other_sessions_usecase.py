from src.modules.auth.domain.services.user_session_domain_service import (
    UserSessionDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, InvalidError, ServerError


class RevokeOtherSessionsUseCase:
    """Revoke every active user session except the caller's current session."""

    def __init__(self, user_session_domain_service: UserSessionDomainService):
        self.user_session_domain_service = user_session_domain_service

    async def execute(self, user_id: int, current_session_uuid: str | None) -> None:
        try:
            if not current_session_uuid:
                raise InvalidError(error="Current session is required")
            await self.user_session_domain_service.revoke_all_except_current(
                user_id=user_id,
                current_session_uuid=current_session_uuid,
            )
        except DomainError:
            raise
        except Exception as exc:
            raise ServerError(
                error="Failed to revoke other sessions",
                internal_details=str(exc),
            ) from exc
