from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class TestEmailMessage:
    __test__ = False
    """
    Data required for sending a template test email.
    """

    email_account_uuid: str
    recipient_email: str
    subject: str
    body_html: str
    body_text: str

    preheader: str | None = None
    from_name: str | None = None


class TestEmailSenderInterface(ABC):
    __test__ = False
    """
    Interface for sending a test email through a connected account.
    """

    @abstractmethod
    async def send(
        self,
        *,
        message: TestEmailMessage,
        organization_id: int,
        actor_id: int,
    ) -> dict[str, str | datetime | Any]:
        """
        Sends the supplied test-email message.
        """
        raise NotImplementedError