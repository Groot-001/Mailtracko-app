from dataclasses import dataclass


@dataclass(slots=True)
class CampaignAudience:
    """Audience review summary. Recipients are persisted in campaign_recipients."""

    estimated_recipient_count: int = 0
    duplicate_contacts_removed: int = 0
    excluded_contacts_count: int = 0

    def __post_init__(self) -> None:
        for field_name, value in (
            ("estimated_recipient_count", self.estimated_recipient_count),
            ("duplicate_contacts_removed", self.duplicate_contacts_removed),
            ("excluded_contacts_count", self.excluded_contacts_count),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")
            if value < 0:
                raise ValueError(f"{field_name} cannot be negative")
        if self.duplicate_contacts_removed + self.excluded_contacts_count > self.estimated_recipient_count:
            raise ValueError("Removed contacts cannot exceed the estimated audience")

    @property
    def final_recipient_count(self) -> int:
        return max(
            self.estimated_recipient_count
            - self.duplicate_contacts_removed
            - self.excluded_contacts_count,
            0,
        )
