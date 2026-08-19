import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pyotp

from src.modules.auth.domain.entities.user_session_entity import UserSessionEntity
from src.modules.auth.domain.repositories.user_totp_recovery_code_repository import (
    IUserTotpRecoveryCodeRepository,
)
from src.modules.auth.domain.repositories.user_totp_secret_repository import IUserTotpSecretRepository
from src.modules.auth.domain.services.user_domain_service import UserDomainService
from src.modules.auth.domain.services.user_session_domain_service import UserSessionDomainService
from src.shared.exceptions.base_exceptions import DomainError, ServerError, UnAuthorizedError
from src.shared.infrastructure.hasher.hasher import HasherService
from src.shared.infrastructure.redis_client import get_redis


class Verify2FALoginUseCase:
    def __init__(
        self,
        user_domain_service: UserDomainService,
        user_session_domain_service: UserSessionDomainService,
        totp_repo: IUserTotpSecretRepository,
        recovery_code_repo: IUserTotpRecoveryCodeRepository,
        hasher_service: HasherService,
    ):
        self.user_domain_service = user_domain_service
        self.user_session_domain_service = user_session_domain_service
        self.totp_repo = totp_repo
        self.recovery_code_repo = recovery_code_repo
        self.hasher_service = hasher_service

    async def execute(
        self,
        temp_token: str,
        code: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        try:
            redis = await get_redis()
            data = await redis.get(f"2fa_temp_token:{temp_token}")
            if not data:
                raise DomainError(error="Invalid or expired temp token")

            payload = json.loads(data)
            user_id = payload["user_id"]
            attempts = int(payload.get("attempts", 0))
            if attempts >= 5:
                await redis.delete(f"2fa_temp_token:{temp_token}")
                raise UnAuthorizedError(error="Too many 2FA attempts. Please sign in again.")

            user = await self.user_domain_service.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise UnAuthorizedError(error="User not found or inactive")

            totp_secret = await self.totp_repo.get_by(user_id=user_id)
            if not totp_secret or not totp_secret.enabled:
                raise DomainError(error="2FA is not enabled for this user")

            valid = False
            totp = pyotp.TOTP(totp_secret.secret)
            if totp.verify(code.strip(), valid_window=1):
                valid = True
            else:
                recovery_codes = await self.recovery_code_repo.filter(
                    user_id=user_id, used_at=None
                )
                for rc in recovery_codes:
                    if self.hasher_service.verify_deterministic_hash(code, rc.code_hash):
                        await self.recovery_code_repo.mark_used(rc.id)
                        valid = True
                        break

            if not valid:
                payload["attempts"] = attempts + 1
                ttl = await redis.ttl(f"2fa_temp_token:{temp_token}")
                await redis.setex(
                    f"2fa_temp_token:{temp_token}",
                    max(1, int(ttl) if ttl and ttl > 0 else 300),
                    json.dumps(payload),
                )
                raise UnAuthorizedError(error="Invalid 2FA code or recovery code")

            # One-time use: consume only after successful verification so a typo does not
            # destroy the challenge, while replay after success remains impossible.
            await redis.delete(f"2fa_temp_token:{temp_token}")

            session_uuid = str(uuid4())
            session = UserSessionEntity(
                uuid=session_uuid,
                user_id=user_id,
                ip_address=ip_address or payload.get("ip_address"),
                user_agent=user_agent or payload.get("user_agent"),
                expires_at=datetime.now(UTC) + timedelta(days=7),
            )
            await self.user_session_domain_service.create_user_session(session)

            user.mark_last_login()
            await self.user_domain_service.update_user(user)

            return {
                "session_uuid": session_uuid,
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
            raise ServerError(error="2FA verification failed", internal_details=str(e)) from e
