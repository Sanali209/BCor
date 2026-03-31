import asyncio
import inspect
import typing
from collections.abc import Callable
from typing import Any

import bubus
import bubus.service
from dishka import AsyncContainer
from loguru import logger
from opentelemetry import trace
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.core.messages import Command, Event, Message
from src.core.unit_of_work import AbstractUnitOfWork

tracer = trace.get_tracer(__name__)


# bubus patches
def _patch_bubus() -> None:
    """Disable bubus built-in loop prevention to allow BCor's context-aware tracing."""
    if hasattr(bubus.service.EventBus, "_would_create_loop"):
        # We disable bubus's internal 2-level recursion limit because BCor
        # implements its own context-aware tracing with a configurable max_trace_depth.
        bubus.service.EventBus._would_create_loop = lambda self, event, handler: False


_patch_bubus()


class MessageBus:
    """Central dispatcher for Commands and Events, powered by bubus.EventBus.

    The MessageBus acts as the mediator between the application layer and 
    infrastructure, ensuring that Commands are executed by a single handler 
    and Events are broadcast to all interested subscribers.

    Architecture Diagram:
    ```mermaid
    graph LR
        Msg[Message] --> Bus[MessageBus]
        Bus -->|Command| H1[Single Handler]
        Bus -->|Event| H2[Many Handlers]
        H1 -.->|Emits| NewEvt[New Events]
        H2 -.->|Triggers| SubTask[Sub-Tasks]
    ```

    Causal Tracing:
        BCor implements "Recursive Context Tracing". Each emitted Event 
        carries a `triggering_message_id`, allowing a full lineage 
        of actions to be reconstructed in logs and Neo4j.

    Rationale:
        We use `bubus` for its lightweight asyncio core, but we patch it 
        to disable its default 2-level loop prevention, as BCor 
        provides its own depth-aware loop control via `max_trace_depth`.

    It supports strict 1-to-1 command routing and 1-to-N event broadcasting.
    It also facilitates domain event collection from the Unit of Work.

    Attributes:
        uow: The active Unit of Work instance.
        max_trace_depth: Maximum recursion depth for message tracing.
        bus: The underlying bubus.EventBus instance.
    """

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        container: AsyncContainer | None = None,
        max_trace_depth: int = 20,
    ) -> None:
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

    def register_command(
        self, cmd_type: type[Command], handler: Callable[..., Any]
    ) -> None:
        """Registers a strict 1-to-1 command handler.

        Command handlers are wrapped with observability (tracing/logging)
        and a retry policy (exponential backoff).

        Args:
            cmd_type: The class of the command to handle.
            handler: The handler function (sync or async).
        """
        wrapper_name = f"command_wrapper_for_{handler.__name__}"

        @retry(
            wait=wait_exponential(multiplier=0.1, min=0.1, max=1.0),
            stop=stop_after_attempt(3),
            reraise=True,
            retry=retry_if_exception_type(Exception),
        )
        async def command_wrapper(command: Command) -> Any:  # noqa: ANN401
            with tracer.start_as_current_span(f"Handle Command: {cmd_type.__name__}") as span:
                logger.info(f"Handling command {cmd_type.__name__}: {command}")
                span.set_attribute("command.type", cmd_type.__name__)

                try:
                    # Resolve dependencies from container for parameters other than 'command'
                    sig = inspect.signature(handler)
                    type_hints = typing.get_type_hints(handler)
                    kwargs = {}
                    for i, (param_name, param) in enumerate(sig.parameters.items()):
                        # Skip the first parameter (the command itself)
                        if i == 0:
                            continue

                        if param_name == "uow":
                            kwargs[param_name] = self.uow
                            continue

                        # Resolve type hint (handles 'from __future__ import annotations')
                        hint = type_hints.get(param_name, param.annotation)

                        # Try to resolve from container if available
                        if self.container and hint != inspect.Parameter.empty:
                            try:
                                kwargs[param_name] = await self.container.get(hint)
                            except Exception as e:
                                logger.debug(
                                    f"DI: Could not resolve {param_name} ({hint}) from container: {e}"
                                )

                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(command, **kwargs)
                    else:
                        result = await asyncio.to_thread(handler, command, **kwargs)

                    return result
                except Exception as e:
                    span.record_exception(e)
                    logger.error(f"Command execution failed: {e}")
                    raise

        command_wrapper.__name__ = wrapper_name
        self.bus.on(cmd_type, command_wrapper)

    def register_event(
        self, evt_type: type[Event], handler: Callable[..., Any]
    ) -> None:
        """Registers a 1-to-N event subscriber.

        Event handlers are wrapped with observability (tracing/logging).
        Failures in event handlers are isolated and do not crash the bus.

        Args:
            evt_type: The class of the event to subscribe to.
            handler: The subscriber function (sync or async).
        """
        wrapper_name = f"event_wrapper_for_{handler.__name__}"

        async def event_wrapper(event: Event) -> None:
            with tracer.start_as_current_span(f"Handle Event: {evt_type.__name__}") as span:
                logger.info(f"Handling event {evt_type.__name__} with {handler.__name__}")
                span.set_attribute("event.type", evt_type.__name__)
                span.set_attribute("handler.name", handler.__name__)

                try:
                    # Resolve dependencies from container for parameters other than 'event'
                    sig = inspect.signature(handler)
                    type_hints = typing.get_type_hints(handler)
                    kwargs = {}
                    for i, (param_name, param) in enumerate(sig.parameters.items()):
                        # Skip the first parameter (the event itself)
                        if i == 0:
                            continue

                        if param_name == "uow":
                            kwargs[param_name] = self.uow
                            continue

                        # Resolve type hint (handles 'from __future__ import annotations')
                        hint = type_hints.get(param_name, param.annotation)

                        # Try to resolve from container if available
                        if self.container and hint != inspect.Parameter.empty:
                            try:
                                kwargs[param_name] = await self.container.get(hint)
                            except Exception as e:
                                logger.debug(
                                    f"DI: Could not resolve {param_name} ({hint}) from container: {e}"
                                )

                    if asyncio.iscoroutinefunction(handler):
                        await handler(event, **kwargs)
                    else:
                        await asyncio.to_thread(handler, event, **kwargs)

                    await self._publish_collected_events(event)
                except Exception as e:
                    span.record_exception(e)
                    logger.exception(f"Isolated failure in event handler {handler.__name__}: {e}")
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
        await self._publish_collected_events(message)
        await message.event_result(raise_if_any=True, raise_if_none=False)
        return message

    async def _publish_collected_events(self, parent_message: Message) -> None:
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
