import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path

from aiosmtplib import SMTP
from jinja2 import Environment, FileSystemLoader

from src.core.config.settings import config
from src.shared.infrastructure.logger import logger
from src.shared.infrastructure.notification.interface.notification_interface import INotification

TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent.parent.parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
ASSETS_DIR = Path(__file__).resolve().parents[6] / "assets"
EMAIL_ASSETS = {
    "logo_src": ("mailtracko-logo", ASSETS_DIR / "logo.png"),
    "facebook_src": ("mailtracko-facebook", ASSETS_DIR / "social" / "facebook.png"),
    "x_src": ("mailtracko-x", ASSETS_DIR / "social" / "x.png"),
    "linkedin_src": ("mailtracko-linkedin", ASSETS_DIR / "social" / "linkedin.png"),
    "instagram_src": ("mailtracko-instagram", ASSETS_DIR / "social" / "instagram.png"),
    "youtube_src": ("mailtracko-youtube", ASSETS_DIR / "social" / "youtube.png"),
    "thread_src": ("mailtracko-thread", ASSETS_DIR / "social" / "thread.png"),
}
_jinja_env.globals["year"] = datetime.now(UTC).year
for source_name, (cid, _) in EMAIL_ASSETS.items():
    _jinja_env.globals[source_name] = f"cid:{cid}"


@dataclass
class EmailMessageData:
    subject: str
    template_name: str
    context: dict
    recipient: list[str]


class EmailNotification(INotification[EmailMessageData]):
    async def send(self, message: EmailMessageData):
        if not message.recipient:
            raise ValueError("Recipient list cannot be empty")

        template = _jinja_env.get_template(message.template_name)
        context = {**message.context, "base_url": config.APP_URL}
        html_body = template.render(**context)

        msg = EmailMessage()
        msg["To"] = ", ".join(message.recipient)
        msg["Subject"] = message.subject
        msg["From"] = f"{config.EMAIL_FROM_NAME} <{config.EMAIL_FROM}>"
        msg.set_content("Please view this email in an HTML-compatible viewer.")
        msg.add_alternative(html_body, subtype="html")

        # Embed branding as MIME related images. This avoids broken images when
        # APP_URL is localhost/private and does not depend on an external CDN.
        # Gmail, Apple Mail and most major clients render these CID assets.
        html_part = msg.get_payload()[-1]
        for cid, asset_path in EMAIL_ASSETS.values():
            if asset_path.exists():
                html_part.add_related(
                    asset_path.read_bytes(),
                    maintype="image",
                    subtype="png",
                    cid=f"<{cid}>",
                    filename=asset_path.name,
                    disposition="inline",
                )

        host = config.SMTP_HOST.strip()
        username = config.SMTP_USERNAME.strip()
        password = config.SMTP_PASSWORD.strip()
        from_address = config.EMAIL_FROM.strip()
        security = config.SMTP_SECURITY.strip().lower()

        if not host or host.lower() in {"mailpit", "localhost", "127.0.0.1"}:
            raise RuntimeError(
                "Real transactional email is not configured: SMTP_HOST must point to a real SMTP provider."
            )
        if security not in {"starttls", "ssl"}:
            raise RuntimeError("SMTP_SECURITY must be either 'starttls' or 'ssl'.")
        if config.SMTP_REQUIRE_AUTH and (not username or not password):
            raise RuntimeError(
                "Real transactional email is not configured: SMTP_USERNAME and SMTP_PASSWORD are required."
            )
        if not from_address or "@" not in from_address:
            raise RuntimeError("EMAIL_FROM must be a valid sender email address.")
        if host.lower() == "smtp.gmail.com":
            expected_port = 587 if security == "starttls" else 465
            if config.SMTP_PORT != expected_port:
                raise RuntimeError(
                    f"Gmail SMTP with {security} requires port {expected_port}."
                )

        # Use a bounded retry loop because real SMTP endpoints can be briefly
        # unavailable. Never retry indefinitely.
        attempts = max(1, config.SMTP_MAX_RETRIES)
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            smtp = SMTP(
                hostname=host,
                port=config.SMTP_PORT,
                timeout=config.SMTP_TIMEOUT_SECONDS,
                use_tls=security == "ssl",
                start_tls=security == "starttls",
            )
            try:
                await smtp.connect()
                if username and password:
                    await smtp.login(username, password)
                await smtp.send_message(msg)
                logger.info("Email sent to %s: %s", msg["To"], msg["Subject"])
                return
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Email send attempt %d/%d failed for %s: %s (SMTP host=%s, port=%s)",
                    attempt,
                    attempts,
                    msg["To"],
                    msg["Subject"],
                    host,
                    config.SMTP_PORT,
                )
                if attempt < attempts:
                    await asyncio.sleep(config.SMTP_RETRY_DELAY_SECONDS * attempt)
            finally:
                try:
                    await smtp.quit()
                except Exception:
                    pass

        assert last_error is not None
        raise last_error
