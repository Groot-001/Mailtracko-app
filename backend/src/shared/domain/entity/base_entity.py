from dataclasses import dataclass, field, asdict, is_dataclass
from datetime import UTC, datetime
from uuid import uuid4

from src.shared.domain.events.base_domain_events import DomainEvent


@dataclass
class BaseEntity:
    id: int | None = None
    uuid: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def mark_updated(self):
        self.updated_at = datetime.now(UTC)

    def add_event(self, event: DomainEvent):
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = self._events[:]
        self._events.clear()
        return events

    def to_cache_dict(self) -> dict:
        if is_dataclass(self):
            data = asdict(self)
        else:
            data = dict(self.__dict__)
        data.pop("_events", None)
        for key, value in list(data.items()):
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
