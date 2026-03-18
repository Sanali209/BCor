from typing import Callable, Type, Optional, Any
import asyncio
import inspect

from dishka import AsyncContainer
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
    
    The MessageBus acts as the mediator between the application layer and 
    domain handlers. It supports strict 1-to-1 command routing and 
    1-to-N event broadcasting. It also facilitates domain event collection 
    from the Unit of Work.

    Attributes:
        uow: The active Unit of Work instance.
        max_trace_depth: Maximum recursion depth for message tracing.
        bus: The underlying bubus.EventBus instance.
    """

    def __init__(self, uow: AbstractUnitOfWork, container: Optional[AsyncContainer] = None, max_trace_depth: int = 20):
        """Initializes the MessageBus with a Unit of Work and optional DI container.

        Args:
            uow: The Unit of Work to associate with the bus.
            container: Optional Dishka container for dependency resolution.
            max_trace_depth: Max depth to prevent infinite loops in handlers.
        """
        self.uow = uow
        self.container = container
        self.max_trace_depth = max_trace_depth
        self.bus = bubus.EventBus()

    def register_command(self, cmd_type: Type[Command], handler: Callable):
        """Registers a strict 1-to-1 command handler.

        Command handlers are wrapped with observability (tracing/logging) 
        and a retry policy (exponential backoff).

        Args:
            cmd_type: The class of the command to handle.
            handler: The handler function (sync or async).
        """
        # Create a uniquely named wrapper for the handler to avoid bubus warnings
        wrapper_name = f"command_wrapper_for_{handler.__name__}"

        @retry(
            wait=wait_exponential(multiplier=0.1, min=0.1, max=1.0),
            stop=stop_after_attempt(3),
            reraise=True,
            retry=retry_if_exception_type(Exception),
        )
        async def command_wrapper(command: cmd_type):
            with tracer.start_as_current_span(
                f"Handle Command: {cmd_type.__name__}"
            ) as span:
                logger.info(f"Handling command {cmd_type.__name__}: {command}")
                span.set_attribute("command.type", cmd_type.__name__)

                try:
                    # Resolve dependencies from container for parameters other than 'command'
                    sig = inspect.signature(handler)
                    kwargs = {}
                    for i, (param_name, param) in enumerate(sig.parameters.items()):
                        # Skip the first parameter (the command itself)
                        if i == 0:
                            continue
                        
                        if param_name == "uow":
                            kwargs[param_name] = self.uow
                            continue
                        
                        # Try to resolve from container if available
                        if self.container and param.annotation != inspect.Parameter.empty:
                            try:
                                # We use the annotation as the key for DI
                                kwargs[param_name] = await self.container.get(param.annotation)
                            except Exception as e:
                                logger.debug(f"DI: Could not resolve {param_name} ({param.annotation}) from container: {e}")

                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(command, **kwargs)
                    else:
                        result = await asyncio.to_thread(handler, command, **kwargs)

                    await self._publish_collected_events(command)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    logger.error(f"Command execution failed: {e}")
                    raise

        command_wrapper.__name__ = wrapper_name
        self.bus.on(cmd_type, command_wrapper)

    def register_event(self, evt_type: Type[Event], handler: Callable):
        """Registers a 1-to-N event subscriber.

        Event handlers are wrapped with observability (tracing/logging).
        Failures in event handlers are isolated and do not crash the bus.

        Args:
            evt_type: The class of the event to subscribe to.
            handler: The subscriber function (sync or async).
        """
        wrapper_name = f"event_wrapper_for_{handler.__name__}"

        async def event_wrapper(event: evt_type):
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

    async def dispatch(self, message: Message) -> Message:
        """Dispatches a message to its registered handlers.

        This is the main entrypoint for processing commands and events.
        It awaits handler completion and bubbles up critical errors.

        Args:
            message: The Command or Event instance to dispatch.

        Returns:
            The original message after processing.
        """
        await self.bus.dispatch(message)
        await message.event_result(raise_if_any=True, raise_if_none=False)
        return message

    async def _publish_collected_events(self, parent_message: Message):
        """Publishes accumulated events from the UoW back into the bus.

        This method supports causality tracing and infinite loop detection
        by maintaining a trace stack for messages.

        Args:
            parent_message: The message that triggered the event collection.

        Raises:
            RuntimeError: If the trace depth exceedes max_trace_depth.
        """
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
                await new_event.event_result(raise_if_any=True, raise_if_none=False)
