from enum import StrEnum


class CampaignType(StrEnum):
    """Defines the supported campaign execution types."""

    REGULAR = "regular"
    SEQUENCE = "sequence"
    AB_TEST = "ab_test"
