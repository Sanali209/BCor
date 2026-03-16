from typing import Any, Callable, Dict, Type, Awaitable, List
import asyncio

import bubus
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.messages import Message, Command, Event
from src.core.unit_of_work import AbstractUnitOfWork
from src.core.monads import BusinessResult, failure

class MessageBus:
    """Central dispatcher for Commands and Events, wrapping `bubus.EventBus` for events."""

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
        self.bus = bubus.EventBus()
        self.command_handlers: Dict[Type[Command], Callable[..., Any]] = {}
        # Start bubus background loop early so tests don't hang?
        # bubus.EventBus requires an active event loop for async operations.
        # Actually EventBus in bubus might just start its own background tasks on dispatch.

    def register_command(self, cmd_type: Type[Command], handler: Callable[..., Any], with_retry: bool = False):
        """Register a single handler for a specific Command type."""
        # Wrap handler with retry if requested
        if with_retry:
            handler = retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                reraise=True
            )(handler)

        self.command_handlers[cmd_type] = handler

    def register_event(self, evt_type: Type[Event], handler: Callable[..., Any], with_retry: bool = False):
        """Register an event subscriber directly on bubus."""
        if with_retry:
            handler = retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                reraise=True
            )(handler)

        async def wrapped_handler(event: evt_type):
            try:
                # Execute the actual synchronous or asynchronous handler logic
                if asyncio.iscoroutinefunction(handler):
                    await handler(event, self.uow)
                else:
                    # Run sync handlers safely in a threadpool so it doesn't block async execution
                    await asyncio.to_thread(handler, event, self.uow)

                # Collect events after successful handler execution
                await self._publish_collected_events()
            except Exception as e:
                # Events isolate failures
                print(f"Isolated failure in event handler {handler.__name__}: {e}")

        self.bus.on(evt_type, wrapped_handler)

    async def handle_command(self, command: Command) -> BusinessResult:
        """Process a Command. Command routing is strictly 1-to-1."""
        handler = self.command_handlers.get(type(command))
        if not handler:
            raise Exception(f"No handler registered for command: {type(command)}")

        # Execute the handler (fail-fast: exceptions bubble up)
        if asyncio.iscoroutinefunction(handler):
            result = await handler(command, self.uow)
        else:
            result = await asyncio.to_thread(handler, command, self.uow)

        # Collect generated domain events from UoW
        await self._publish_collected_events()

        return result

    async def _publish_collected_events(self):
        """Publish all accumulated events from the UoW into bubus."""
        events = list(self.uow.collect_new_events())
        if events:
            # bubus expects async dispatch
            for new_event in events:
                await self.bus.dispatch(new_event)
