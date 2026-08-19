from src.modules.auth.domain.entities.user_activity_entity import UserActivityEntity
from src.modules.auth.domain.enums.user_activity_enums import UserActivityTypeEnum
from src.modules.auth.domain.events.auth_password_domain_events import PasswordChangedEvent
from src.modules.auth.domain.services.user_account_domain_service import UserAccountDomainService
from src.modules.auth.domain.services.user_domain_service import UserDomainService
from src.modules.auth.domain.services.user_session_domain_service import UserSessionDomainService
from src.shared.exceptions.base_exceptions import DomainError, InvalidError, ServerError, UnAuthorizedError
from src.shared.infrastructure.hasher.hasher import HasherService
from src.shared.mediator.mediator import mediator


class ChangePasswordUseCase:
    def __init__(
        self,
        user_domain_service: UserDomainService,
        user_account_domain_service: UserAccountDomainService,
        user_session_domain_service: UserSessionDomainService,
        hasher_service: HasherService,
        user_activity_repo,
    ):
        self.user_domain_service = user_domain_service
        self.user_account_domain_service = user_account_domain_service
        self.user_session_domain_service = user_session_domain_service
        self.hasher_service = hasher_service
        self.user_activity_repo = user_activity_repo

    async def execute(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        confirm_password: str,
        current_session_uuid: str | None = None,
    ) -> dict:
        try:
            if new_password != confirm_password:
                raise InvalidError(error="New password and confirm password do not match")

            account = await self.user_account_domain_service.get_user_account_by_user_id(
                user_id=user_id, type="password",
            )
            if not account or not account.hashed_password:
                raise UnAuthorizedError(error="No password account found")

            if not self.user_domain_service.verify_password(current_password, account.hashed_password):
                raise UnAuthorizedError(error="Current password is incorrect")

            self.user_domain_service.validate_password(new_password)
            new_hash = self.hasher_service.hash(new_password)
            account.update_password(new_hash)
            await self.user_account_domain_service.update_user_account(account)

            if current_session_uuid:
                await self.user_session_domain_service.revoke_all_except_current(
                    user_id=user_id, current_session_uuid=current_session_uuid,
                )
            else:
                await self.user_session_domain_service.revoke_all_sessions_for_user(user_id=user_id)

            user = await self.user_domain_service.get_active_user_by_id(user_id)
            if user:
                user.add_event(PasswordChangedEvent(user_id=user_id))
                for event in user.pull_events():
                    await mediator.publish(event)

            activity = UserActivityEntity(
                user_id=user_id,
                activity_type=UserActivityTypeEnum.PASSWORD_CHANGED.value,
                description="Password changed",
                metadata={},
            )
            await self.user_activity_repo.add(activity)

            return {"message": "Password changed successfully"}

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to change password", internal_details=str(e)) from e
