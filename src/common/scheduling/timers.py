"""Asynchronous timer and scheduling utilities.

Replaces legacy appGlue/timertreaded.py with modern asyncio-based scheduling.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


class AsyncTimer:
    """An asyncio-based timer for periodic or delayed execution.
    
    Ported and modernized from legacy Timer/TimerManager class.
    """

    def __init__(
        self,
        interval: float,
        callback: Callable[..., Awaitable[Any] | Any],
        *args: Any,
        repeat: bool = True,
        delay: float = 0,
        **kwargs: Any,
    ):
        """Initialize the timer.
        
        Args:
            interval: Time in seconds between executions.
            callback: Function to execute. Can be sync or async.
            repeat: Whether to run repeatedly (True) or once (False).
            delay: Initial delay before the first execution starts.
            *args: Arguments for callback.
            **kwargs: Keyword arguments for callback.
        """
        self.interval = interval
        self.callback = callback
        self.args = args
        self.kwargs = kwargs
        self.repeat = repeat
        self.delay = delay
        self._task: asyncio.Task | None = None
        self._is_running = False

    def start(self) -> None:
        """Start the timer task in the current event loop."""
        if self._is_running:
            return
        
        self._is_running = True
        self._task = asyncio.create_task(self._run())
        logger.debug(f"AsyncTimer started: {self.callback.__name__} (interval: {self.interval}s)")

    async def _run(self) -> None:
        """Internal execution loop."""
        try:
            if self.delay > 0:
                await asyncio.sleep(self.delay)

            while self._is_running:
                # Execute callback
                try:
                    if asyncio.iscoroutinefunction(self.callback):
                        await self.callback(*self.args, **self.kwargs)
                    else:
                        self.callback(*self.args, **self.kwargs)
                except Exception as e:
                    logger.error(f"Error in AsyncTimer callback {self.callback.__name__}: {e}")

                if not self.repeat:
                    break

                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            logger.debug(f"AsyncTimer cancelled: {self.callback.__name__}")
        finally:
            self._is_running = False

    def stop(self) -> None:
        """Stop the timer task."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.debug(f"AsyncTimer stopped: {self.callback.__name__}")

    @property
    def is_running(self) -> bool:
        """Check if the timer is currently running."""
        return self._is_running


def set_timeout(delay: float, callback: Callable[..., Any], *args: Any, **kwargs: Any) -> AsyncTimer:
    """Utility to run a callback once after a delay (resembling JS setTimeout)."""
    timer = AsyncTimer(0, callback, *args, repeat=False, delay=delay, **kwargs)
    timer.start()
    return timer


def set_interval(interval: float, callback: Callable[..., Any], *args: Any, **kwargs: Any) -> AsyncTimer:
    """Utility to run a callback periodically (resembling JS setInterval)."""
    timer = AsyncTimer(interval, callback, *args, repeat=True, **kwargs)
    timer.start()
    return timer
