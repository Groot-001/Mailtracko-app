import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.modules.auth.domain.entities.user_activity_entity import UserActivityEntity
from src.modules.auth.domain.entities.user_session_entity import UserSessionEntity
from src.modules.auth.domain.enums.user_activity_enums import UserActivityTypeEnum
from src.modules.auth.domain.repositories.user_activity_repository import IUserActivityRepository
from src.modules.auth.domain.repositories.user_totp_secret_repository import IUserTotpSecretRepository
from src.modules.auth.domain.services.user_account_domain_service import UserAccountDomainService
from src.modules.auth.domain.services.user_domain_service import UserDomainService
from src.modules.auth.domain.services.user_session_domain_service import UserSessionDomainService
from src.shared.exceptions.base_exceptions import DomainError, ServerError, UnAuthorizedError
from src.shared.infrastructure.redis_client import get_redis


class LoginUserUseCase:
    def __init__(
        self,
        user_domain_service: UserDomainService,
        user_account_domain_service: UserAccountDomainService,
        user_session_domain_service: UserSessionDomainService,
        user_activity_repo: IUserActivityRepository,
        totp_repo: IUserTotpSecretRepository,
    ):
        self.user_domain_service = user_domain_service
        self.user_account_domain_service = user_account_domain_service
        self.user_session_domain_service = user_session_domain_service
        self.user_activity_repo = user_activity_repo
        self.totp_repo = totp_repo

    async def _create_session(
        self, user_id: int, ip_address: str | None, user_agent: str | None
    ) -> str:
        session_uuid = str(uuid4())
        session = UserSessionEntity(
            uuid=session_uuid,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        await self.user_session_domain_service.create_user_session(session)
        return session_uuid

    async def _create_2fa_challenge(
        self, user_id: int, ip_address: str | None, user_agent: str | None
    ) -> str:
        """Issue a short-lived, server-side MFA challenge without creating a session."""
        temp_token = str(uuid4())
        redis = await get_redis()
        await redis.setex(
            f"2fa_temp_token:{temp_token}",
            300,
            json.dumps(
                {
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "attempts": 0,
                }
            ),
        )
        await self.user_activity_repo.add(
            UserActivityEntity(
                user_id=user_id,
                activity_type=UserActivityTypeEnum.TWO_FA_CHALLENGE.value,
                description="2FA login challenge issued",
                metadata={"ip_address": ip_address, "user_agent": user_agent},
            )
        )
        return temp_token

    async def oauth_login(
        self, user, ip_address: str | None = None, user_agent: str | None = None
    ) -> dict:
        try:
            assert user.id is not None, "User ID must be set"

            totp_secret = await self.totp_repo.get_by(user_id=user.id)
            if totp_secret and totp_secret.enabled:
                temp_token = await self._create_2fa_challenge(user.id, ip_address, user_agent)
                return {
                    "requires_2fa": True,
                    "temp_token": temp_token,
                    "requires_email_verification": not user.is_email_verified(),
                    "user": {
                        "uuid": user.uuid,
                        "full_name": user.full_name,
                        "email": user.email,
                        "theme": user.theme,
                    },
                }

            user.mark_last_login()
            await self.user_domain_service.update_user(user)
            session_uuid = await self._create_session(user.id, ip_address, user_agent)
            return {
                "session_uuid": session_uuid,
                "requires_2fa": False,
                "requires_email_verification": not user.is_email_verified(),
                "user": {
                    "uuid": user.uuid,
                    "full_name": user.full_name,
                    "email": user.email,
                    "theme": user.theme,
                },
            }
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="OAuth login failed", internal_details=str(e)) from e

    async def execute(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        try:
            email = self.user_domain_service.validate_email(email)

            user = await self.user_domain_service.get_user_by_email(email)
            if not user:
                raise UnAuthorizedError(error="Invalid email or password")

            if user.has_active_deletion_schedule():
                user.cancel_scheduled_deletion()
                await self.user_domain_service.update_user(user)

            if not user.is_active:
                raise UnAuthorizedError(error="Account is deactivated")

            user_id = user.id
            if not user_id:
                raise UnAuthorizedError(error="User not found")

            account = await self.user_account_domain_service.get_user_account_by_user_id(
                user_id=user_id, type="password"
            )
            if not account or not account.hashed_password:
                raise UnAuthorizedError(error="Invalid email or password")

            if not self.user_domain_service.verify_password(password, account.hashed_password):
                raise UnAuthorizedError(error="Invalid email or password")

            totp_secret = await self.totp_repo.get_by(user_id=user_id)
            if totp_secret and totp_secret.enabled:
                temp_token = await self._create_2fa_challenge(user_id, ip_address, user_agent)
                return {
                    "requires_2fa": True,
                    "requires_email_verification": not user.is_email_verified(),
                    "temp_token": temp_token,
                    "user": {
                        "uuid": user.uuid,
                        "full_name": user.full_name,
                        "email": user.email,
                        "theme": user.theme,
                    },
                }

            user.mark_last_login()
            await self.user_domain_service.update_user(user)

            session_uuid = await self._create_session(user_id, ip_address, user_agent)

            if ip_address:
                existing_sessions = await self.user_session_domain_service.list_sessions_by_user_id(user_id)
                known_ips = {s.ip_address for s in existing_sessions if s.ip_address and s.uuid != session_uuid}
                if ip_address not in known_ips:
                    activity = UserActivityEntity(
                        user_id=user_id,
                        activity_type=UserActivityTypeEnum.SUSPICIOUS_LOGIN.value,
                        description=f"Login from new IP: {ip_address}",
                        metadata={"ip_address": ip_address, "user_agent": user_agent},
                    )
                    await self.user_activity_repo.add(activity)

            return {
                "session_uuid": session_uuid,
                "requires_email_verification": not user.is_email_verified(),
                "user": {
                    "uuid": user.uuid,
                    "full_name": user.full_name,
                    "email": user.email,
                    "theme": user.theme,
                },
            }
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="An error occurred during login", internal_details=str(e)) from e
