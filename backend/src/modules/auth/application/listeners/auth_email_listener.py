from src.modules.auth.domain.events.auth_domain_events import UserCreatedEvent, UserUpdatedEvent
from src.modules.auth.domain.events.auth_email_domain_events import (
    EmailVerificationTokenCreatedEvent,
    EmailVerifiedEvent,
)
from src.modules.auth.domain.events.auth_password_domain_events import (
    ForgotPasswordLinkCreatedEvent,
    PasswordChangedEvent,
)
from src.modules.auth.domain.events.auth_session_domain_events import UserSessionUpdatedEvent
from src.shared.infrastructure.logger import logger
from src.shared.infrastructure.notification.adapter.email.email_notification import (
    EmailMessageData,
    EmailNotification,
)
from src.shared.mediator.listener import listener

email_notification = EmailNotification()


@listener(UserCreatedEvent)
async def on_user_created(event: UserCreatedEvent):
    logger.info(
        "[AuthListener] User created: user_id=%s email=%s full_name=%s",
        event.user_id, event.email, event.full_name,
    )


@listener(UserUpdatedEvent)
async def on_user_updated(event: UserUpdatedEvent):
    logger.info(
        "[AuthListener] User updated: user_id=%s prev=%s value=%s",
        event.user_id, event.prev_value, event.value,
    )


@listener(EmailVerifiedEvent)
async def on_email_verified(event: EmailVerifiedEvent):
    logger.info(
        "[AuthListener] Email verified: user_id=%s email=%s",
        event.user_id, event.email,
    )
    message = EmailMessageData(
        subject="Welcome to MailTracko! 🎉",
        template_name="auth/welcome.html",
        context={"user_name": event.full_name},
        recipient=[event.email],
    )
    try:
        await email_notification.send(message)
    except Exception:
        logger.exception("Failed to send welcome email to %s", event.email)


@listener(PasswordChangedEvent)
async def on_password_changed(event: PasswordChangedEvent):
    logger.info(
        "[AuthListener] Password changed: user_id=%s", event.user_id,
    )


@listener(UserSessionUpdatedEvent)
async def on_user_session_updated(event: UserSessionUpdatedEvent):
    logger.info(
        "[AuthListener] Session updated: session_uuid=%s value=%s",
        event.session_uuid, event.value,
    )


@listener(EmailVerificationTokenCreatedEvent)
async def on_email_verification_token_created(event: EmailVerificationTokenCreatedEvent):
    message = EmailMessageData(
        subject="Verify your email",
        template_name="auth/verify_email.html",
        context={"verification_code": event.token, "user_name": event.full_name},
        recipient=[event.email],
    )
    try:
        await email_notification.send(message)
    except Exception:
        logger.exception("Failed to send verification email to %s", event.email)
        raise


@listener(ForgotPasswordLinkCreatedEvent)
async def on_forgot_password_link_created(event: ForgotPasswordLinkCreatedEvent):
    message = EmailMessageData(
        subject="Reset your password",
        template_name="auth/reset_password.html",
        context={"reset_code": event.link, "user_name": event.full_name},
        recipient=[event.email],
    )
    try:
        await email_notification.send(message)
    except Exception:
        logger.exception("Failed to send password reset email to %s", event.email)
