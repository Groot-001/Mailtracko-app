import asyncio
import secrets
import smtplib
import string
from datetime import UTC, datetime, timedelta

from src.core.config.settings import config
from src.modules.email_account.domain.constants import CODE_EXPIRE_HOURS
from src.modules.email_account.domain.entities.email_account_entity import (
    EmailAccountEntity,
)
from src.modules.email_account.domain.entities.smtp_config_entity import (
    SmtpConfigEntity,
)
from src.modules.email_account.domain.enums.email_account_enums import (
    EmailAccountProvider,
    EmailAccountStatus,
)
from src.modules.email_account.domain.services.email_account_domain_service import (
    EmailAccountDomainService,
)
from src.modules.email_account.infrastructure.constants import (
    IMAP_SSL_PORTS,
    SMTP_SSL_PORTS,
    SMTP_STARTTLS_PORTS,
)
from src.modules.email_account.presentation.schemas.email_account_schemas import (
    ConnectSmtpRequestSchema,
)
from src.shared.exceptions.base_exceptions import (
    ConflictError,
    DomainError,
    InvalidError,
    ServerError,
)
from src.shared.infrastructure.encryption.fernet_encryption import encrypt
from src.shared.infrastructure.hasher.hasher import HasherService


class SmtpConnectUseCase:
    def __init__(
        self,
        email_account_domain_service: EmailAccountDomainService,
        hasher_service: HasherService,
    ):
        self.email_account_domain_service = email_account_domain_service
        self.hasher_service = hasher_service

    async def execute(
        self,
        payload: ConnectSmtpRequestSchema,
        organization_id: int,
        actor_id: int,
    ) -> dict:
        try:
            existing = (
                await self.email_account_domain_service.get_by_email_and_organization(
                    email=payload.email,
                    organization_id=organization_id,
                )
            )
            if existing:
                raise ConflictError(
                    error="This email is already connected to your organization"
                )

            count = await self.email_account_domain_service.count_by_organization(
                organization_id
            )
            if count >= config.MAX_EMAIL_ACCOUNTS_PER_ORG:
                raise InvalidError(
                    error=f"Your plan allows a maximum of {config.MAX_EMAIL_ACCOUNTS_PER_ORG} email account(s)"
                )

            await self._test_smtp(
                payload.smtp_host,
                payload.smtp_port,
                payload.smtp_username,
                payload.smtp_password,
            )
            if payload.imap_host and payload.imap_port:
                await self._test_imap(
                    payload.imap_host,
                    payload.imap_port,
                    payload.smtp_username,
                    payload.smtp_password,
                )

            code = self._generate_code()
            code_hash = self.hasher_service.deterministic_hash(code)

            smtp_config = SmtpConfigEntity(
                encrypted_password=encrypt(payload.smtp_password),
                smtp_host=payload.smtp_host,
                smtp_port=payload.smtp_port,
                smtp_username=payload.smtp_username,
                imap_host=payload.imap_host,
                imap_port=payload.imap_port,
                verification_code_hash=code_hash,
                verification_sent_at=datetime.now(UTC),
                verification_attempts=1,
                code_expires_at=datetime.now(UTC) + timedelta(hours=CODE_EXPIRE_HOURS),
            )
            created_smtp = await self.email_account_domain_service.create_smtp_config(
                smtp_config
            )

            account = EmailAccountEntity(
                organization_id=organization_id,
                provider=EmailAccountProvider.SMTP.value,
                email=payload.email,
                sender_name=payload.sender_name,
                status=EmailAccountStatus.PENDING_VERIFICATION.value,
                smtp_config_id=created_smtp.id,
                reply_to=payload.reply_to,
                signature=payload.signature,
                sending_limit=config.PROVIDER_DEFAULT_SENDING_LIMITS.get("smtp", 100),
                created_by_id=actor_id,
            )
            created = await self.email_account_domain_service.create_account(account)

            await self._send_email(
                payload.smtp_host,
                payload.smtp_port,
                payload.smtp_username,
                payload.smtp_password,
                payload.email,
                code,
            )

            return {
                "uuid": created.uuid,
                "email": created.email,
                "provider": created.provider,
                "status": created.status,
                "message": "Verification code sent to your email",
            }
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to connect SMTP account", internal_details=str(e)
            ) from e

    async def test_credentials(self, payload: ConnectSmtpRequestSchema) -> dict:
        """Validate provider credentials without persisting secrets or sending mail."""
        await self._test_smtp(
            payload.smtp_host,
            payload.smtp_port,
            payload.smtp_username,
            payload.smtp_password,
        )
        imap_tested = bool(payload.imap_host and payload.imap_port)
        if payload.imap_host and payload.imap_port:
            await self._test_imap(
                payload.imap_host,
                payload.imap_port,
                payload.smtp_username,
                payload.smtp_password,
            )
        return {
            "smtp": "verified",
            "imap": "verified" if imap_tested else "not_configured",
        }

    async def _test_smtp(
        self, host: str, port: int, username: str, password: str
    ) -> None:
        def _sync():
            if port in SMTP_SSL_PORTS:
                s = smtplib.SMTP_SSL(host, port, timeout=10)
            else:
                s = smtplib.SMTP(host, port, timeout=10)
                if port in SMTP_STARTTLS_PORTS:
                    s.starttls()
            with s:
                s.login(username, password)

        try:
            await asyncio.to_thread(_sync)
        except smtplib.SMTPAuthenticationError:
            raise InvalidError(
                error="SMTP authentication failed. Check your username and password."
            )
        except smtplib.SMTPException as e:
            raise InvalidError(error=f"SMTP connection failed: {e}")
        except OSError as e:
            raise InvalidError(error=f"Cannot connect to SMTP server: {e}")

    async def _test_imap(
        self, host: str, port: int, username: str, password: str
    ) -> None:
        import imaplib

        def _sync():
            if port in IMAP_SSL_PORTS:
                s = imaplib.IMAP4_SSL(host, port)
            else:
                s = imaplib.IMAP4(host, port)
            with s:
                s.login(username, password)
                s.logout()

        try:
            await asyncio.to_thread(_sync)
        except imaplib.IMAP4.error as e:
            raise InvalidError(error=f"IMAP connection failed: {e}")
        except OSError as e:
            raise InvalidError(error=f"Cannot connect to IMAP server: {e}")

    def _generate_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(6))

    async def _send_email(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        to_email: str,
        code: str,
    ) -> None:
        def _sync():
            subject = "Verify your email account"
            body = f"Your verification code is: {code}\n\nEnter this code to activate your email account."
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
            raise ServerError(
                error=f"Failed to send verification email: {e}", internal_details=str(e)
            ) from e
