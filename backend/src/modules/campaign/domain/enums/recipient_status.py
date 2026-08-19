from enum import StrEnum


class RecipientStatus(StrEnum):
    """Defines the campaign delivery state for an individual recipient."""

    PENDING = "pending"
    QUEUED = "queued"
    HOLDOUT = "holdout"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"
    UNSUBSCRIBED = "unsubscribed"
    SKIPPED = "skipped"
    STOPPED = "stopped"
