from enum import StrEnum


class CampaignGoal(StrEnum):
    """Defines the primary objective of a campaign."""

    SALES = "sales"
    LEAD_GENERATION = "lead_generation"
    OUTREACH = "outreach"
    FOLLOW_UP = "follow_up"
    NEWSLETTER = "newsletter"
    CUSTOM = "custom"
