import asyncio
import base64
import html
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage
from email.utils import formataddr
from typing import Any

import httpx

from src.modules.email_account.domain.enums.email_account_enums import (
    EmailAccountProvider,
)
from src.modules.email_account.domain.services.email_account_domain_service import (
    EmailAccountDomainService,
)
from src.modules.email_account.infrastructure.constants import (
    SMTP_SSL_PORTS,
    SMTP_STARTTLS_PORTS,
)
from src.modules.email_account.infrastructure.oauth.google_mail_oauth_client import (
    GoogleMailOAuthClient,
)
from src.modules.email_template.infrastructure.email_sender.interface.test_email_sender_interface import (
    TestEmailMessage,
    TestEmailSenderInterface,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    InvalidError,
    NotFoundError,
    ServerError,
)
from src.shared.infrastructure.encryption.fernet_encryption import (
    decrypt,
)


class ConnectedEmailAccountTestSender(
    TestEmailSenderInterface
):
    """
    Sends template test emails through connected email accounts.
    """

    def __init__(
        self,
        email_account_domain_service: EmailAccountDomainService,
        google_mail_oauth_client: GoogleMailOAuthClient,
    ):
        self.email_account_domain_service = (
            email_account_domain_service
        )
        self.google_mail_oauth_client = (
            google_mail_oauth_client
        )

    async def send(
        self,
        *,
        message: TestEmailMessage,
        organization_id: int,
        actor_id: int,
    ) -> dict[str, str | datetime | Any]:
        """
        Sends a test email using the selected connected account.
        """
        try:
            account = (
                await self.email_account_domain_service
                .get_account_by_uuid(
                    message.email_account_uuid
                )
            )

            if (
                not account
                or account.organization_id
                != organization_id
            ):
                raise NotFoundError(
                    error="Email account not found"
                )

            if not account.is_active():
                raise InvalidError(
                    error=(
                        "The selected email account is not active"
                    )
                )

            account.reset_daily_if_new_day()

            if not account.can_send():
                raise InvalidError(
                    error=(
                        "The selected email account cannot "
                        "send emails at this time"
                    )
                )

            rendered_body_html = (
                self._inject_preheader(
                    body_html=message.body_html,
                    preheader=message.preheader,
                )
            )

            sender_name = (
                message.from_name
                or account.sender_name
                or account.email
            )

            provider_result: dict[str, Any] = {}

            if (
                account.provider
                == EmailAccountProvider.SMTP.value
            ):
                await self._send_smtp(
                    account=account,
                    recipient_email=(
                        message.recipient_email
                    ),
                    subject=message.subject,
                    body_html=rendered_body_html,
                    body_text=message.body_text,
                    sender_name=sender_name,
                )

            elif (
                account.provider
                == EmailAccountProvider.GMAIL.value
            ):
                provider_result = await self._send_gmail(
                    account=account,
                    recipient_email=(
                        message.recipient_email
                    ),
                    subject=message.subject,
                    body_html=rendered_body_html,
                    body_text=message.body_text,
                    sender_name=sender_name,
                )

            else:
                raise InvalidError(
                    error=(
                        "Unsupported email account provider"
                    )
                )

            sent_at = datetime.now(UTC)

            account.daily_sent_count += 1
            account.last_sent_date = sent_at.date()
            account.last_used_at = sent_at
            account.updated_by_id = actor_id
            account.mark_updated()

            await self.email_account_domain_service.update_account(
                account
            )

            return {
                "recipient_email": (
                    message.recipient_email
                ),
                "sender_email": account.email,
                "provider": account.provider,
                "provider_message_id": provider_result.get("id"),
                "provider_thread_id": provider_result.get("threadId"),
                "sent_at": sent_at,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to send template test email",
                internal_details=str(e),
            ) from e

    async def _send_smtp(
        self,
        *,
        account,
        recipient_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        sender_name: str,
    ) -> None:
        """
        Sends a multipart test email through SMTP.
        """
        if account.smtp_config_id is None:
            raise InvalidError(
                error=(
                    "SMTP configuration is missing "
                    "for the selected account"
                )
            )

        smtp_config = (
            await self.email_account_domain_service
            .get_smtp_config(
                account.smtp_config_id
            )
        )

        if not smtp_config:
            raise InvalidError(
                error="SMTP configuration not found"
            )

        password = decrypt(
            smtp_config.encrypted_password
        )

        email_message = self._build_mime_message(
            sender_email=account.email,
            sender_name=sender_name,
            recipient_email=recipient_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            reply_to=account.reply_to,
        )

        def send_synchronously() -> None:
            if (
                smtp_config.smtp_port
                in SMTP_SSL_PORTS
            ):
                smtp_client = smtplib.SMTP_SSL(
                    smtp_config.smtp_host,
                    smtp_config.smtp_port,
                    timeout=20,
                )
            else:
                smtp_client = smtplib.SMTP(
                    smtp_config.smtp_host,
                    smtp_config.smtp_port,
                    timeout=20,
                )

                if (
                    smtp_config.smtp_port
                    in SMTP_STARTTLS_PORTS
                ):
                    smtp_client.starttls()

            with smtp_client:
                smtp_client.login(
                    smtp_config.smtp_username,
                    password,
                )
                smtp_client.send_message(
                    email_message
                )

        try:
            await asyncio.to_thread(
                send_synchronously
            )

        except smtplib.SMTPAuthenticationError as e:
            raise InvalidError(
                error=(
                    "SMTP authentication failed. "
                    "Reconnect the email account."
                )
            ) from e

        except (
            smtplib.SMTPException,
            OSError,
        ) as e:
            raise ServerError(
                error=(
                    "Failed to send test email through SMTP"
                ),
                internal_details=str(e),
            ) from e

    async def _send_gmail(
        self,
        *,
        account,
        recipient_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        sender_name: str,
    ) -> dict[str, Any]:
        """
        Sends a multipart test email through Gmail API.
        """
        if account.oauth_config_id is None:
            raise InvalidError(
                error=(
                    "OAuth configuration is missing "
                    "for the selected Gmail account"
                )
            )

        oauth_config = (
            await self.email_account_domain_service
            .get_oauth_config(
                account.oauth_config_id
            )
        )

        if not oauth_config:
            raise InvalidError(
                error="Gmail OAuth configuration not found"
            )

        refresh_token = decrypt(
            oauth_config.encrypted_refresh_token
        )

        email_message = self._build_mime_message(
            sender_email=account.email,
            sender_name=sender_name,
            recipient_email=recipient_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            reply_to=account.reply_to,
        )

        encoded_message = (
            base64.urlsafe_b64encode(
                email_message.as_bytes()
            )
            .decode("utf-8")
            .rstrip("=")
        )

        try:
            token_result = (
                await self.google_mail_oauth_client
                .refresh_access_token(
                    refresh_token
                )
            )

            access_token = token_result.get(
                "access_token"
            )

            if not access_token:
                raise InvalidError(
                    error=(
                        "Unable to refresh Gmail access token"
                    )
                )

            return await self.google_mail_oauth_client.send_raw_message(
                access_token=access_token,
                raw_message=encoded_message,
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code in {
                400,
                401,
                403,
            }:
                account.mark_reconnect_required()

                await self.email_account_domain_service.update_account(
                    account
                )

                raise InvalidError(
                    error=(
                        "Gmail authorization has expired. "
                        "Reconnect the email account."
                    )
                ) from e

            raise ServerError(
                error=(
                    "Failed to send test email through Gmail"
                ),
                internal_details=e.response.text,
            ) from e

        except httpx.RequestError as e:
            raise ServerError(
                error=(
                    "Failed to connect to the Gmail API"
                ),
                internal_details=str(e),
            ) from e

    def _build_mime_message(
        self,
        *,
        sender_email: str,
        sender_name: str,
        recipient_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        reply_to: str | None,
    ) -> EmailMessage:
        """
        Builds a multipart MIME email with plain-text and HTML parts.
        """
        email_message = EmailMessage()

        email_message["From"] = formataddr(
            (
                sender_name,
                sender_email,
            )
        )
        email_message["To"] = recipient_email
        email_message["Subject"] = subject

        if reply_to:
            email_message["Reply-To"] = reply_to

        email_message.set_content(
            body_text
        )
        email_message.add_alternative(
            body_html,
            subtype="html",
        )

        return email_message

    def _inject_preheader(
        self,
        *,
        body_html: str,
        preheader: str | None,
    ) -> str:
        """
        Inserts hidden preview text before the visible email body.
        """
        if not preheader:
            return body_html

        escaped_preheader = html.escape(
            preheader,
            quote=True,
        )

        hidden_preheader = (
            '<div style="display:none;'
            'font-size:1px;'
            'line-height:1px;'
            'max-height:0;'
            'max-width:0;'
            'opacity:0;'
            'overflow:hidden;'
            'mso-hide:all;">'
            f"{escaped_preheader}"
            "</div>"
        )

        return (
            hidden_preheader
            + body_html
        )