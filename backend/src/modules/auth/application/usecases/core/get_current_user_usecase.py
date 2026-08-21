from src.modules.auth.domain.repositories.user_totp_secret_repository import IUserTotpSecretRepository
from src.modules.auth.domain.services.user_account_domain_service import UserAccountDomainService
from src.modules.auth.domain.services.user_domain_service import UserDomainService
from src.modules.organization.domain.services.organization_domain_service import (
    OrganizationDomainService,
)
from src.modules.organization.domain.services.organization_member_domain_service import (
    OrganizationMemberDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, InvalidError, ServerError


class GetCurrentUserUseCase:
    def __init__(
        self,
        user_domain_service: UserDomainService,
        user_account_domain_service: UserAccountDomainService,
        organization_member_domain_service: OrganizationMemberDomainService,
        organization_domain_service: OrganizationDomainService,
        totp_repo: IUserTotpSecretRepository,
    ):
        self.user_domain_service = user_domain_service
        self.user_account_domain_service = user_account_domain_service
        self.organization_member_domain_service = organization_member_domain_service
        self.organization_domain_service = organization_domain_service
        self.totp_repo = totp_repo

    async def execute(self, user_id: int) -> dict:
        try:
            user = await self.user_domain_service.get_active_user_by_id(user_id)
            if not user:
                raise InvalidError(error="User not found")

            totp_secret = await self.totp_repo.get_by(user_id=user_id)
            password_account = await self.user_account_domain_service.get_user_account_by_user_id(
                user_id=user_id, type="password"
            )

            result = {
                "uuid": user.uuid,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": user.profile_image,
                "timezone": user.timezone,
                "phone": user.phone,
                "country_code": user.country_code,
                "location": user.location,
                "theme": user.theme,
                "is_2fa_enabled": bool(totp_secret and totp_secret.enabled),
                "has_password": bool(password_account and password_account.hashed_password),
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "role": None,
                "organization_name": None,
                "organization_uuid": None,
                "member_status": None,
                "account_status": "active" if user.is_active else "inactive",
            }

            member = await self.organization_member_domain_service.get_active_member_by_user_id(user_id)
            if member:
                result["role"] = member.role_code
                result["member_status"] = member.status
                org = await self.organization_domain_service.get_organization_by_id(member.organization_id)
                if org:
                    result["organization_name"] = org.name
                    result["organization_uuid"] = org.uuid

            return result
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to retrieve user", internal_details=str(e)) from e
