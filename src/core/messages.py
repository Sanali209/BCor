from bubus import BaseEvent


class Message(BaseEvent):
    """Base class for all messages using bubus.BaseEvent (which extends Pydantic BaseModel)."""

    pass


class Command(Message):
    """Base class for commands. Commands are routed strictly to one handler."""

    pass


class Event(Message):
    """Base class for events. Events are broadcast to multiple handlers."""

    pass
