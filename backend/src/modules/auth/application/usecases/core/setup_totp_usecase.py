import base64
import io
import secrets

import pyotp
import qrcode

from src.modules.auth.domain.entities.user_totp_recovery_code_entity import UserTotpRecoveryCodeEntity
from src.modules.auth.domain.entities.user_totp_secret_entity import UserTotpSecretEntity
from src.modules.auth.domain.repositories.user_totp_recovery_code_repository import (
    IUserTotpRecoveryCodeRepository,
)
from src.modules.auth.domain.repositories.user_totp_secret_repository import IUserTotpSecretRepository
from src.shared.exceptions.base_exceptions import DomainError, ServerError
from src.shared.infrastructure.hasher.hasher import HasherService


def _generate_recovery_codes(count: int = 8) -> list[str]:
    codes = []
    for _ in range(count):
        raw = secrets.token_hex(6).upper()
        code = f"{raw[:4]}-{raw[4:8]}-{raw[8:12]}"
        codes.append(code)
    return codes


class SetupTotpUseCase:
    def __init__(
        self,
        totp_repo: IUserTotpSecretRepository,
        recovery_code_repo: IUserTotpRecoveryCodeRepository,
        hasher_service: HasherService,
    ):
        self.totp_repo = totp_repo
        self.recovery_code_repo = recovery_code_repo
        self.hasher_service = hasher_service

    async def execute(self, user_id: int, email: str) -> dict:
        try:
            existing = await self.totp_repo.get_by(user_id=user_id)
            if existing and existing.enabled:
                raise DomainError(error="2FA is already enabled")

            secret = pyotp.random_base32()
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(name=email, issuer_name="MailTracko")

            qr = qrcode.make(provisioning_uri)
            buf = io.BytesIO()
            qr.save(buf, format="PNG")
            qr_base64 = base64.b64encode(buf.getvalue()).decode()

            if existing:
                existing.secret = secret
                existing.enabled = False
                await self.totp_repo.update(existing)
            else:
                entity = UserTotpSecretEntity(
                    user_id=user_id,
                    secret=secret,
                    enabled=False,
                )
                await self.totp_repo.add(entity)

            old_codes = await self.recovery_code_repo.filter(user_id=user_id)
            for oc in old_codes:
                await self.recovery_code_repo.delete(oc.id)

            raw_codes = _generate_recovery_codes(8)
            hashed_codes = [
                self.hasher_service.deterministic_hash(c) for c in raw_codes
            ]
            for hc in hashed_codes:
                rc_entity = UserTotpRecoveryCodeEntity(
                    user_id=user_id,
                    code_hash=hc,
                )
                await self.recovery_code_repo.add(rc_entity)

            return {
                "secret": secret,
                "provisioning_uri": provisioning_uri,
                "qr_code": f"data:image/png;base64,{qr_base64}",
                "recovery_codes": raw_codes,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to setup 2FA", internal_details=str(e)) from e
