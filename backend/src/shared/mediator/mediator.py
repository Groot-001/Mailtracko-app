import inspect
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from src.shared.infrastructure.logger import logger

Handler = Callable[[Any], Any]


class Mediator:
    """In-memory mediator for loosely-coupled event-driven architecture."""

    def __init__(self):
        self._handlers: dict[type, list[Handler]] = defaultdict(list)
        self._before_hooks: list[Callable] = []
        self._after_hooks: list[Callable] = []

    def register(self, event_type: type, handler: Handler):
        self._handlers[event_type].append(handler)

    def add_before_hook(self, hook: Callable):
        self._before_hooks.append(hook)

    def add_after_hook(self, hook: Callable):
        self._after_hooks.append(hook)

    async def publish(self, event: Any, *, raise_on_error: bool = False):
        logger.info("[Mediator] Publishing event: %s", type(event).__name__)
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        logger.info(
            "[Mediator] Found %d handlers for event: %s",
            len(handlers),
            event_type.__name__,
        )

        for hook in self._before_hooks:
            try:
                if inspect.iscoroutinefunction(hook):
                    await hook(event)
                else:
                    hook(event)
            except Exception as e:
                logger.error("[Mediator Before Hook Error] %s", str(e))
                if raise_on_error:
                    raise

        results = []

        for handler in handlers:
            try:
                logger.info(
                    "[Mediator] -> [%s] Executing handler: %s ",
                    event.__class__.__name__,
                    handler.__name__,
                )
                if inspect.iscoroutinefunction(handler):
                    results.append(await handler(event))
                else:
                    results.append(handler(event))
            except Exception as e:
                logger.error("[Mediator Handler Error] %s: %s", handler.__name__, str(e))
                if raise_on_error:
                    raise

        for hook in self._after_hooks:
            try:
                if inspect.iscoroutinefunction(hook):
                    await hook(event)
                else:
                    hook(event)
            except Exception as e:
                logger.error("[Mediator After Hook Error] %s", str(e))
                if raise_on_error:
                    raise

        return results


mediator = Mediator()
