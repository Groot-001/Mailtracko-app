from types import ModuleType, SimpleNamespace
import sys

import pytest

# The project declares aiosmtplib in pyproject/uv.lock. The CI sandbox used for
# this isolated unit test may not have optional runtime dependencies installed,
# so provide a minimal import stub and replace it with FakeSMTP below.
_aiosmtplib = ModuleType("aiosmtplib")
_aiosmtplib.SMTP = object
sys.modules.setdefault("aiosmtplib", _aiosmtplib)

from src.shared.infrastructure.notification.adapter.email import email_notification as module
from src.shared.infrastructure.notification.adapter.email.email_notification import (
    EmailMessageData,
    EmailNotification,
)


class FakeSMTP:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.connected = False
        self.login_args = None
        self.sent = None
        self.quit_called = False
        self.__class__.instances.append(self)

    async def connect(self):
        self.connected = True

    async def login(self, username, password):
        self.login_args = (username, password)

    async def send_message(self, message):
        self.sent = message

    async def quit(self):
        self.quit_called = True


def make_config(**overrides):
    values = dict(
        APP_URL="http://localhost:3000",
        EMAIL_FROM_NAME="MailTracko",
        EMAIL_FROM="sender@gmail.com",
        SMTP_HOST="smtp.gmail.com",
        SMTP_PORT=587,
        SMTP_USERNAME="sender@gmail.com",
        SMTP_PASSWORD="abcdefghijklmnop",
        SMTP_SECURITY="starttls",
        SMTP_REQUIRE_AUTH=True,
        SMTP_TIMEOUT_SECONDS=30,
        SMTP_MAX_RETRIES=1,
        SMTP_RETRY_DELAY_SECONDS=0,
        CLOUDINARY_CLOUD_NAME="",
        CLOUDINARY_FOLDER="mailtracko",
    )
    values.update(overrides)
    return SimpleNamespace(**values)



@pytest.mark.asyncio
async def test_real_email_adapter_rejects_local_smtp_catcher_async(monkeypatch):
    monkeypatch.setattr(module, "config", make_config(SMTP_HOST="mailpit", SMTP_PORT=1025))
    with pytest.raises(RuntimeError, match="real SMTP provider"):
        await EmailNotification().send(
            EmailMessageData(
                subject="test",
                template_name="system/smtp_test.html",
                context={},
                recipient=["recipient@example.com"],
            )
        )


@pytest.mark.asyncio
async def test_gmail_requires_starttls_port_587(monkeypatch):
    monkeypatch.setattr(module, "config", make_config(SMTP_PORT=1025))
    with pytest.raises(RuntimeError, match="requires port 587"):
        await EmailNotification().send(
            EmailMessageData(
                subject="test",
                template_name="system/smtp_test.html",
                context={},
                recipient=["recipient@example.com"],
            )
        )


@pytest.mark.asyncio
async def test_real_email_adapter_uses_authenticated_gmail_starttls(monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(module, "config", make_config())
    monkeypatch.setattr(module, "SMTP", FakeSMTP)

    await EmailNotification().send(
        EmailMessageData(
            subject="MailTracko SMTP test",
            template_name="system/smtp_test.html",
            context={},
            recipient=["recipient@example.com"],
        )
    )

    smtp = FakeSMTP.instances[-1]
    assert smtp.kwargs["hostname"] == "smtp.gmail.com"
    assert smtp.kwargs["port"] == 587
    assert smtp.kwargs["use_tls"] is False
    assert smtp.kwargs["start_tls"] is True
    assert smtp.login_args == ("sender@gmail.com", "abcdefghijklmnop")
    assert smtp.sent["To"] == "recipient@example.com"
    assert smtp.quit_called is True


@pytest.mark.asyncio
async def test_email_branding_assets_are_embedded_as_cid(monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(module, "config", make_config())
    monkeypatch.setattr(module, "SMTP", FakeSMTP)

    await EmailNotification().send(
        EmailMessageData(
            subject="MailTracko branding test",
            template_name="auth/verify_email.html",
            context={"verification_code": "123456", "recipient_email": "recipient@example.com"},
            recipient=["recipient@example.com"],
        )
    )

    message = FakeSMTP.instances[-1].sent
    html_parts = [part for part in message.walk() if part.get_content_type() == "text/html"]
    assert len(html_parts) == 1
    html = html_parts[0].get_content()
    assert "cid:mailtracko-logo" in html
    assert "cid:mailtracko-facebook" in html
    content_ids = {part.get("Content-ID") for part in message.walk() if part.get("Content-ID")}
    assert "<mailtracko-logo>" in content_ids
    assert "<mailtracko-facebook>" in content_ids
    assert "<mailtracko-x>" in content_ids
