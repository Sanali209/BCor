from typing import Any, Callable, Dict, Type, List
import logging
import asyncio

import bubus

from src.core.messages import Message, Command, Event
from src.core.unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)

class MessageBus:
    """Central dispatcher for Commands and Events, powered by bubus.EventBus.

    This replaces the custom dictionary-based loop with bubus.EventBus.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
        self.bus = bubus.EventBus()

    def register_command(self, cmd_type: Type[Command], handler: Callable):
        """Register a strict 1-to-1 command handler."""
        # Create a uniquely named wrapper for the handler to avoid bubus warnings
        wrapper_name = f"command_wrapper_for_{handler.__name__}"

        async def command_wrapper(command: cmd_type):
            logger.debug(f"Handling command {command}")
            if asyncio.iscoroutinefunction(handler):
                result = await handler(command, uow=self.uow)
            else:
                result = await asyncio.to_thread(handler, command, uow=self.uow)

            await self._publish_collected_events()
            return result

        command_wrapper.__name__ = wrapper_name
        self.bus.on(cmd_type, command_wrapper)

    def register_event(self, evt_type: Type[Event], handler: Callable):
        """Register a 1-to-N event subscriber."""
        wrapper_name = f"event_wrapper_for_{handler.__name__}"

        async def event_wrapper(event: evt_type):
            try:
                logger.debug(f"Handling event {event} with {handler.__name__}")
                if asyncio.iscoroutinefunction(handler):
                    await handler(event, uow=self.uow)
                else:
                    await asyncio.to_thread(handler, event, uow=self.uow)

                await self._publish_collected_events()
            except Exception as e:
                logger.exception(f"Isolated failure in event handler {handler.__name__}: {e}")

        event_wrapper.__name__ = wrapper_name
        self.bus.on(evt_type, event_wrapper)

    async def dispatch(self, message: Message):
        """Entrypoint for processing messages via bubus."""
        results = await self.bus.dispatch(message)
        return results

    async def _publish_collected_events(self):
        """Publish all accumulated events from the UoW into bubus."""
        events = list(self.uow.collect_new_events())
        if events:
            for new_event in events:
                await self.bus.dispatch(new_event)
