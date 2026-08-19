from enum import StrEnum


class ScheduleType(StrEnum):
    """Defines how a campaign is scheduled for execution."""

    IMMEDIATE = "immediate"
    ONE_TIME = "one_time"
    RECURRING = "recurring"
