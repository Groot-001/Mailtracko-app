from enum import StrEnum


class SenderSelectionType(StrEnum):
    """Defines how sender accounts are selected during execution."""

    SINGLE = "single"
    ROUND_ROBIN = "round_robin"
    SMART_ROTATION = "smart_rotation"
