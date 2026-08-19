from enum import StrEnum


class StopReason(StrEnum):
    """Defines why campaign or sequence execution stopped."""

    COMPLETED = "completed"
    USER_CANCELLED = "user_cancelled"
    REPLIED = "replied"
    CLICKED = "clicked"
    MEETING = "meeting"
    CUSTOM_EVENT = "custom_event"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    SENDER_LIMIT = "sender_limit"
    NO_RECIPIENTS = "no_recipients"
    NO_SENDERS = "no_senders"
    TEMPLATE_ERROR = "template_error"
    WORKER_FAILURE = "worker_failure"
    SYSTEM_ERROR = "system_error"
