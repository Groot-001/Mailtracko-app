from enum import StrEnum


class CampaignPriority(StrEnum):
    """Defines campaign execution priority."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
