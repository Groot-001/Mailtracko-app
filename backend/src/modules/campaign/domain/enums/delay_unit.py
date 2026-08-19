from enum import StrEnum


class DelayUnit(StrEnum):
    """Defines the units supported for sequence delays."""

    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
