from enum import StrEnum


class SequenceStepType(StrEnum):
    """Defines the supported step types inside an email sequence."""

    EMAIL = "email"
    DELAY = "delay"
    CONDITION = "condition"
