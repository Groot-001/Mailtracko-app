from dataclasses import dataclass, field
from typing import Any

from src.shared.integrations.events.event_types import EventType
from src.shared.infrastructure.logger import logger


@dataclass(kw_only=True)
class Event:
    """Domain event carrying a type and payload."""

    type: EventType
    data: dict[str, Any] = field(default_factory=dict)


class EventDispatcher:
    """Simple event dispatcher that logs events.

    Can be extended later with real pub/sub or message broker integration.
    """

    def dispatch(self, event: Event) -> None:
        """Dispatch an event by logging it."""
        logger.info("Event dispatched: %s | data=%s", event.type, event.data)
