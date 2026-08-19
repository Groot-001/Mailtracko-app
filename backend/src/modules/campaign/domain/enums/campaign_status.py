from enum import StrEnum


class CampaignStatus(StrEnum):
    """Defines the overall lifecycle state of a campaign."""

    DRAFT = "draft"
    READY = "ready"
    SCHEDULED = "scheduled"
    LAUNCHING = "launching"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    ARCHIVED = "archived"
