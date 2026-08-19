from enum import StrEnum


class ABTestStatus(StrEnum):
    """Defines the lifecycle state of campaign A/B testing."""

    DISABLED = "disabled"
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    WINNER_SELECTED = "winner_selected"
