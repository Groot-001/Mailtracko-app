from enum import StrEnum


class SequenceStatus(StrEnum):
    """Defines the execution state of a campaign sequence."""

    NOT_STARTED = "not_started"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"
