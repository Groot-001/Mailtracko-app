from enum import StrEnum


class CampaignValidationStatus(StrEnum):
    """Defines the severity of campaign readiness validation."""

    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
