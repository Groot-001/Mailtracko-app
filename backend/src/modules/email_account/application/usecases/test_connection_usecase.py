import asyncio
import smtplib

from src.modules.email_account.domain.enums.email_account_enums import EmailAccountHealthStatus
from src.modules.email_account.domain.services.email_account_domain_service import EmailAccountDomainService
from src.modules.email_account.infrastructure.constants import IMAP_SSL_PORTS, SMTP_SSL_PORTS, SMTP_STARTTLS_PORTS
from src.modules.email_account.infrastructure.health.health_score import compute_health_score
from src.modules.email_account.infrastructure.oauth.google_mail_oauth_client import GoogleMailOAuthClient
from src.shared.exceptions.base_exceptions import DomainError, NotFoundError, ServerError
from src.shared.infrastructure.encryption.fernet_encryption import decrypt


class TestConnectionUseCase:
    __test__ = False

    def __init__(
        self,
        email_account_domain_service: EmailAccountDomainService,
        google_mail_oauth_client: GoogleMailOAuthClient | None = None,
    ):
        self.email_account_domain_service = email_account_domain_service
        self.google_mail_oauth_client = google_mail_oauth_client

    async def execute(self, account_uuid: str, organization_id: int, actor_id: int | None = None) -> dict:
        try:
            account = await self.email_account_domain_service.get_account_by_uuid(account_uuid)
            if not account or account.organization_id != organization_id:
                raise NotFoundError(error="Email account not found")

            healthy = False
            details = ""
            smtp_host = None

            if account.provider == "smtp":
                healthy, details = await self._test_smtp(account.smtp_config_id)
                if account.smtp_config_id:
                    config = await self.email_account_domain_service.get_smtp_config(account.smtp_config_id)
                    if config:
                        smtp_host = config.smtp_host
            elif account.is_oauth():
                healthy, details = await self._test_oauth(account.oauth_config_id, account.provider)
            else:
                details = f"Unknown provider: {account.provider}"

            new_status = EmailAccountHealthStatus.HEALTHY.value if healthy else EmailAccountHealthStatus.UNHEALTHY.value
            account.health_status = new_status

            score, health_details = await asyncio.to_thread(
                compute_health_score,
                account={
                    "email": account.email,
                    "provider": account.provider,
                    "health_status": new_status,
                    "daily_sent_count": account.daily_sent_count,
                    "sending_limit": account.sending_limit,
                    "last_sent_date": account.last_sent_date,
                },
                smtp_host=smtp_host,
            )
            account.health_score = score
            account.health_details = health_details

            account.mark_updated()
            if actor_id:
                account.updated_by_id = actor_id
            await self.email_account_domain_service.update_account(account)

            return {
                "uuid": account.uuid,
                "email": account.email,
                "provider": account.provider,
                "health_status": account.health_status,
                "health_score": account.health_score,
                "health_details": account.health_details,
                "details": details,
            }
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to test connection", internal_details=str(e)) from e

    async def _test_smtp(self, smtp_config_id: int | None) -> tuple[bool, str]:
        if not smtp_config_id:
            return False, "No SMTP configuration found"
        config = await self.email_account_domain_service.get_smtp_config(smtp_config_id)
        if not config:
            return False, "SMTP configuration not found"

        password = decrypt(config.encrypted_password)

        def _sync():
            if config.smtp_port in SMTP_SSL_PORTS:
                s = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=10)
            else:
                s = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=10)
                if config.smtp_port in SMTP_STARTTLS_PORTS:
                    s.starttls()
            with s:
                s.login(config.smtp_username, password)

        try:
            await asyncio.to_thread(_sync)
            if config.imap_host and config.imap_port:
                await self._test_imap(config.imap_host, config.imap_port, config.smtp_username, password)
            return True, "SMTP connection successful"
        except smtplib.SMTPAuthenticationError:
            return False, "SMTP authentication failed"
        except Exception as e:
            return False, f"SMTP connection failed: {e}"

    async def _test_imap(self, host: str, port: int, username: str, password: str) -> None:
        import imaplib
        def _sync():
            if port in IMAP_SSL_PORTS:
                s = imaplib.IMAP4_SSL(host, port)
            else:
                s = imaplib.IMAP4(host, port)
            with s:
                s.login(username, password)
                s.logout()
        await asyncio.to_thread(_sync)

    async def _test_oauth(self, oauth_config_id: int | None, provider: str) -> tuple[bool, str]:
        if not oauth_config_id:
            return False, "No OAuth configuration found"
        config = await self.email_account_domain_service.get_oauth_config(oauth_config_id)
        if not config:
            return False, "OAuth configuration not found"

        refresh_token = decrypt(config.encrypted_refresh_token)
        if not refresh_token:
            return False, "No refresh token available"

        try:
            if provider == "gmail" and self.google_mail_oauth_client:
                await self.google_mail_oauth_client.refresh_access_token(refresh_token)
            else:
                return False, f"No OAuth client configured for {provider}"
            return True, "OAuth token refresh successful"
        except Exception as e:
            return False, f"OAuth token refresh failed: {e}"
