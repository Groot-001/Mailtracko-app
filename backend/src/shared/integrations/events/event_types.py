from enum import StrEnum


class EventType(StrEnum):
    """Event types for the events integration."""

    # User events
    USER_CREATED = "user.created"
