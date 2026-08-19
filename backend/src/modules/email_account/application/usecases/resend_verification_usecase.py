import asyncio
import secrets
import smtplib
import string
from datetime import UTC, datetime, timedelta

from src.modules.email_account.domain.constants import COOLDOWN_SECONDS, CODE_EXPIRE_HOURS, MAX_ATTEMPTS
from src.modules.email_account.infrastructure.constants import SMTP_SSL_PORTS, SMTP_STARTTLS_PORTS
from src.modules.email_account.domain.services.email_account_domain_service import EmailAccountDomainService
from src.shared.exceptions.base_exceptions import DomainError, InvalidError, NotFoundError, ServerError
from src.shared.infrastructure.encryption.fernet_encryption import decrypt
from src.shared.infrastructure.hasher.hasher import HasherService


class ResendVerificationUseCase:

    def __init__(
        self,
        email_account_domain_service: EmailAccountDomainService,
        hasher_service: HasherService,
    ):
        self.email_account_domain_service = email_account_domain_service
        self.hasher_service = hasher_service

    async def execute(
        self,
        account_uuid: str,
        organization_id: int,
    ) -> dict:
        try:
            account = await self.email_account_domain_service.get_account_by_uuid(account_uuid)
            if not account or account.organization_id != organization_id:
                raise NotFoundError(error="Email account not found")

            if not account.is_pending_verification():
                raise InvalidError(error="Email account is not pending verification")

            smtp_config = await self.email_account_domain_service.get_smtp_config(account.smtp_config_id)
            if not smtp_config:
                raise ServerError(error="SMTP configuration not found")

            if smtp_config.verification_attempts >= MAX_ATTEMPTS:
                raise InvalidError(error="Maximum verification attempts reached. Please reconnect the account.")

            if smtp_config.verification_sent_at:
                elapsed = (datetime.now(UTC) - smtp_config.verification_sent_at).total_seconds()
                if elapsed < COOLDOWN_SECONDS:
                    remaining = int(COOLDOWN_SECONDS - elapsed)
                    raise InvalidError(error=f"Please wait {remaining} seconds before requesting a new code")

            code = self._generate_code()
            code_hash = self.hasher_service.deterministic_hash(code)

            smtp_config.verification_code_hash = code_hash
            smtp_config.verification_sent_at = datetime.now(UTC)
            smtp_config.verification_attempts += 1
            smtp_config.code_expires_at = datetime.now(UTC) + timedelta(hours=CODE_EXPIRE_HOURS)
            smtp_config.mark_updated()
            await self.email_account_domain_service.update_smtp_config(smtp_config)

            password = decrypt(smtp_config.encrypted_password)
            await self._send_email(smtp_config.smtp_host, smtp_config.smtp_port, smtp_config.smtp_username, password, account.email, code)

            return {"message": "Verification code resent to your email"}
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to resend verification code", internal_details=str(e)) from e

    def _generate_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(6))

    async def _send_email(self, host: str, port: int, username: str, password: str, to_email: str, code: str) -> None:
        def _sync():
            subject = "Verify your email account"
            body = f"Your new verification code is: {code}\n\nEnter this code to activate your email account."
            msg = f"Subject: {subject}\n\n{body}"
            if port in SMTP_SSL_PORTS:
                s = smtplib.SMTP_SSL(host, port, timeout=10)
            else:
                s = smtplib.SMTP(host, port, timeout=10)
                if port in SMTP_STARTTLS_PORTS:
                    s.starttls()
            with s:
                s.login(username, password)
                s.sendmail(to_email, [to_email], msg.encode("utf-8"))
        try:
            await asyncio.to_thread(_sync)
        except Exception as e:
            raise ServerError(error=f"Failed to send verification email: {e}", internal_details=str(e)) from e
