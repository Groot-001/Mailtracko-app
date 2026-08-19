from enum import StrEnum


class CampaignStep(StrEnum):
    """Defines the current step in the campaign setup workflow."""

    SETUP = "setup"
    AUDIENCE = "audience"
    SENDER = "sender"
    CONTENT = "content"
    SCHEDULE = "schedule"
    REVIEW = "review"
    LAUNCH = "launch"
