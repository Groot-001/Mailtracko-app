from enum import StrEnum


class ContactActivityTypeEnum(StrEnum):
    """Types of activities logged in the contact timeline."""

    IMPORTED = "imported"
    MERGED = "merged"
    EMAIL_SENT = "email_sent"
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    MANUAL_NOTE = "manual_note"


class ImportStatusEnum(StrEnum):
    """Status of an async CSV/Sheets import job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
