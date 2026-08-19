
from enum import StrEnum


class EmailAccountProvider(StrEnum):
    GMAIL = "gmail"
    SMTP = "smtp"


class EmailAccountStatus(StrEnum):
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    RECONNECT_REQUIRED = "reconnect_required"
    DISCONNECTED = "disconnected"


class EmailAccountHealthStatus(StrEnum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"