from enum import StrEnum


class AudienceType(StrEnum):
    """Defines the supported campaign audience sources."""

    LIST = "list"
    SEGMENT = "segment"
    SAVED_FILTER = "saved_filter"
    MANUAL = "manual"
