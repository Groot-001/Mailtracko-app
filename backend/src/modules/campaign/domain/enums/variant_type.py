from enum import StrEnum


class VariantType(StrEnum):
    """Defines the available A/B test variants."""

    A = "a"
    B = "b"
