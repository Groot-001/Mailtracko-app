from src.shared.mediator.mediator import mediator
from src.shared.mediator.registry import registry


def listener(event_type):
    """Decorator that registers a function as a handler for an event type."""

    def wrapper(func):
        mediator.register(event_type, func)
        registry.record(event_type, func)
        return func

    return wrapper
