from typing import Any, Callable, Dict, Type, List
import logging
import asyncio

import bubus

from loguru import logger
from opentelemetry import trace

from src.core.messages import Message, Command, Event
from src.core.unit_of_work import AbstractUnitOfWork

tracer = trace.get_tracer(__name__)

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
            # Observability: Start a trace span and log
            with tracer.start_as_current_span(f"Handle Command: {cmd_type.__name__}") as span:
                logger.info(f"Handling command {cmd_type.__name__}: {command}")
                span.set_attribute("command.type", cmd_type.__name__)

                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(command, uow=self.uow)
                    else:
                        result = await asyncio.to_thread(handler, command, uow=self.uow)

                    await self._publish_collected_events()
                    return result
                except Exception as e:
                    span.record_exception(e)
                    logger.error(f"Command execution failed: {e}")
                    # bubus swallows exceptions, so we re-raise them specifically for fail-fast if needed,
                    # but since dispatch returns EventResults we can just let bubus log it and check results.
                    raise

        command_wrapper.__name__ = wrapper_name
        self.bus.on(cmd_type, command_wrapper)

    def register_event(self, evt_type: Type[Event], handler: Callable):
        """Register a 1-to-N event subscriber."""
        wrapper_name = f"event_wrapper_for_{handler.__name__}"

        async def event_wrapper(event: evt_type):
            # Observability: Start a trace span and log
            with tracer.start_as_current_span(f"Handle Event: {evt_type.__name__}") as span:
                logger.info(f"Handling event {evt_type.__name__} with {handler.__name__}")
                span.set_attribute("event.type", evt_type.__name__)
                span.set_attribute("handler.name", handler.__name__)

                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event, uow=self.uow)
                    else:
                        await asyncio.to_thread(handler, event, uow=self.uow)

                    await self._publish_collected_events()
                except Exception as e:
                    span.record_exception(e)
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
