from src.core.config.settings import config
from src.modules.auth.domain.services.user_domain_service import UserDomainService
from src.modules.auth.domain.services.user_session_domain_service import UserSessionDomainService
from src.modules.organization.domain.enums.organization_enums import OrganizationRoleCodeEnum
from src.modules.organization.domain.services.organization_member_domain_service import (
    OrganizationMemberDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, InvalidError, ServerError


class DeleteAccountUseCase:
    """Schedule safe user-account deletion and revoke all active sessions."""

    def __init__(
        self,
        user_domain_service: UserDomainService,
        user_session_domain_service: UserSessionDomainService,
        organization_member_domain_service: OrganizationMemberDomainService,
    ) -> None:
        self.user_domain_service = user_domain_service
        self.user_session_domain_service = user_session_domain_service
        self.organization_member_domain_service = organization_member_domain_service

    async def execute(self, user_id: int) -> dict:
        try:
            user = await self.user_domain_service.get_active_user_by_id(user_id)
            if not user:
                raise InvalidError(error="User not found")

            membership = (
                await self.organization_member_domain_service.get_active_member_by_user_id(
                    user_id=user_id
                )
            )
            if membership and membership.role_code == OrganizationRoleCodeEnum.OWNER.value:
                raise InvalidError(
                    error=(
                        "Organization owners cannot delete their user account while they own an "
                        "active workspace. Transfer ownership or schedule organization deletion first."
                    ),
                    errors={"code": "OWNER_ACCOUNT_DELETE_BLOCKED"},
                )

            user.schedule_deletion(grace_days=config.ACCOUNT_DELETION_GRACE_DAYS)
            await self.user_domain_service.update_user(user)
            await self.user_session_domain_service.revoke_all_sessions_for_user(user_id)

            return {
                "message": (
                    f"Your account is scheduled for deletion in "
                    f"{config.ACCOUNT_DELETION_GRACE_DAYS} days. "
                    "Log in within this period to cancel the deletion."
                ),
                "scheduled_deletion_at": user.scheduled_deletion_at.isoformat(),
            }
        except DomainError:
            raise
        except Exception as exc:
            raise ServerError(
                error="Failed to schedule account deletion",
                internal_details=str(exc),
            ) from exc
