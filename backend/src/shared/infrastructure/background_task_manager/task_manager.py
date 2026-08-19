import asyncio
from collections.abc import Coroutine
from typing import Any

from src.shared.infrastructure.logger import logger


class BackgroundTaskManager:
    """Manages periodic background tasks with graceful shutdown support."""

    def __init__(self):
        self._tasks: list[asyncio.Task] = []
        self._running = False

    def add_task(self, coro: Coroutine[Any, Any, None]) -> asyncio.Task:
        task = asyncio.create_task(coro)
        self._tasks.append(task)
        return task

    async def start(self):
        self._running = True
        logger.info("[BackgroundTaskManager] Started %d task(s)", len(self._tasks))

    async def stop(self):
        self._running = False
        for task in self._tasks:
            task.cancel()
        results = await asyncio.gather(*self._tasks, return_exceptions=True)
        for task, result in zip(self._tasks, results, strict=False):
            if isinstance(result, asyncio.CancelledError):
                logger.debug("[BackgroundTaskManager] Task %s cancelled", task.get_name())
            elif isinstance(result, Exception):
                logger.error("[BackgroundTaskManager] Task %s error: %s", task.get_name(), result)
        self._tasks.clear()
        logger.info("[BackgroundTaskManager] All tasks stopped")


task_manager = BackgroundTaskManager()
