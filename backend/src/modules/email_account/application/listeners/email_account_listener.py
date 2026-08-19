from src.modules.email_account.domain.events.email_account_domain_events import (
    EmailAccountConnectedEvent,
    EmailAccountDisconnectedEvent,
    EmailAccountVerifiedEvent,
)
from src.shared.infrastructure.logger import logger
from src.shared.mediator.listener import listener


@listener(EmailAccountConnectedEvent)
async def on_email_account_connected(event: EmailAccountConnectedEvent) -> None:
    logger.info("[EmailListener] Email account connected: %s (%s)", event.email, event.provider)


@listener(EmailAccountVerifiedEvent)
async def on_email_account_verified(event: EmailAccountVerifiedEvent) -> None:
    logger.info("[EmailListener] Email account verified: %s", event.email)


@listener(EmailAccountDisconnectedEvent)
async def on_email_account_disconnected(event: EmailAccountDisconnectedEvent) -> None:
    logger.info("[EmailListener] Email account disconnected: %s", event.email)
