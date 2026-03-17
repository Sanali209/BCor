from typing import Callable, Type
import asyncio

import bubus
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from loguru import logger
from opentelemetry import trace

from src.core.messages import Message, Command, Event
from src.core.unit_of_work import AbstractUnitOfWork

tracer = trace.get_tracer(__name__)


import bubus.service


def _patch_bubus():
    """Disable bubus built-in loop prevention to allow BCor's context-aware tracing."""
    if hasattr(bubus.service.EventBus, "_would_create_loop"):
        # We disable bubus's internal 2-level recursion limit because BCor 
        # implements its own context-aware tracing with a configurable max_trace_depth.
        bubus.service.EventBus._would_create_loop = lambda self, event, handler: False


_patch_bubus()


class MessageBus:
    """Central dispatcher for Commands and Events, powered by bubus.EventBus.
    
    Implements context-aware tracing to detect and prevent infinite loops.
    """

    def __init__(self, uow: AbstractUnitOfWork, max_trace_depth: int = 20):
        self.uow = uow
        self.max_trace_depth = max_trace_depth
        self.bus = bubus.EventBus()

    def register_command(self, cmd_type: Type[Command], handler: Callable):
        """Register a strict 1-to-1 command handler."""
        # Create a uniquely named wrapper for the handler to avoid bubus warnings
        wrapper_name = f"command_wrapper_for_{handler.__name__}"

        @retry(
            wait=wait_exponential(multiplier=0.1, min=0.1, max=1.0),
            stop=stop_after_attempt(3),
            reraise=True,
            retry=retry_if_exception_type(Exception),
        )
        async def command_wrapper(command: cmd_type):
            # Observability: Start a trace span and log
            with tracer.start_as_current_span(
                f"Handle Command: {cmd_type.__name__}"
            ) as span:
                logger.info(f"Handling command {cmd_type.__name__}: {command}")
                span.set_attribute("command.type", cmd_type.__name__)

                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(command, uow=self.uow)
                    else:
                        result = await asyncio.to_thread(handler, command, uow=self.uow)

                    await self._publish_collected_events(command)
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
            with tracer.start_as_current_span(
                f"Handle Event: {evt_type.__name__}"
            ) as span:
                logger.info(
                    f"Handling event {evt_type.__name__} with {handler.__name__}"
                )
                span.set_attribute("event.type", evt_type.__name__)
                span.set_attribute("handler.name", handler.__name__)

                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event, uow=self.uow)
                    else:
                        await asyncio.to_thread(handler, event, uow=self.uow)

                    await self._publish_collected_events(event)
                except Exception as e:
                    span.record_exception(e)
                    logger.exception(
                        f"Isolated failure in event handler {handler.__name__}: {e}"
                    )
                    if isinstance(e, RuntimeError) and "Infinite loop detected" in str(e):
                        raise

        event_wrapper.__name__ = wrapper_name
        self.bus.on(evt_type, event_wrapper)

    async def dispatch(self, message: Message):
        """Entrypoint for processing messages via bubus."""
        await self.bus.dispatch(message)
        
        # We MUST await the message completion to catch any critical errors 
        # (like infinite loops) that happened in the background handlers.
        # raise_if_none=False because some events might not have any handlers.
        await message.event_result(raise_if_any=True, raise_if_none=False)
                
        return message

    async def _publish_collected_events(self, parent_message: Message):
        """Publish all accumulated events from the UoW into bubus."""
        events = list(self.uow.collect_new_events())
        if events:
            new_trace = parent_message.trace_stack.copy()
            new_trace.append(type(parent_message).__name__)

            if len(new_trace) > self.max_trace_depth:
                raise RuntimeError(f"Infinite loop detected: trace stack {new_trace}")

            for new_event in events:
                new_event.correlation_id = parent_message.correlation_id
                new_event.trace_stack = new_trace
                await self.bus.dispatch(new_event)
                
                # Await completion to detect critical errors (infinite loops) early and bubble them up
                await new_event.event_result(raise_if_any=True, raise_if_none=False)
