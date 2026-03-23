import uuid

from bubus.models import BaseEvent
from pydantic import Field


class Message(BaseEvent):  # type: ignore[misc]
    """Base class for all messages in the framework.
    """
    correlation_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    trace_stack: list[str] = Field(default_factory=list)

    async def event_result(self, raise_if_any: bool = True, raise_if_none: bool = False) -> None:
        """Stub for event result handling to satisfy MessageBus."""
        pass


class Command(Message):
    """Base class for Commands.

    Commands represent an intention to change state and are routed
    strictly to a single handler.
    """

    pass


class Event(Message):
    """Base class for Events.

    Events represent facts about something that has happened in the
    domain and are broadcast to multiple subscribers.
    """

    pass
