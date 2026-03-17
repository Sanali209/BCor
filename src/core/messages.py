from bubus import BaseEvent


import uuid
from typing import List
from pydantic import Field

class Message(BaseEvent):
    """Base class for all messages using bubus.BaseEvent (which extends Pydantic BaseModel)."""
    correlation_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    trace_stack: List[str] = Field(default_factory=list)


class Command(Message):
    """Base class for commands. Commands are routed strictly to one handler."""

    pass


class Event(Message):
    """Base class for events. Events are broadcast to multiple handlers."""

    pass
