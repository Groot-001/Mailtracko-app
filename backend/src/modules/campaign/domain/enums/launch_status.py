from enum import StrEnum


class LaunchStatus(StrEnum):
    """Defines the execution state of a campaign launch."""

    NOT_STARTED = "not_started"
    VALIDATING = "validating"
    QUEUED = "queued"
    STARTING = "starting"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
