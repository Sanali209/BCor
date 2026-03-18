from bubus import BaseEvent


import uuid
from typing import List
from pydantic import Field

class Message(BaseEvent):
    """Base class for all messages in the framework.
    
    Extends Pydantic BaseModel via bubus.BaseEvent. Supports correlation 
    IDs for distributed tracing and trace stacks for recursion detection.
    
    Attributes:
        correlation_id: Unique string linking related messages across the system.
        trace_stack: List of message types encountered in the current causality chain.
    """
    correlation_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    trace_stack: List[str] = Field(default_factory=list)


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
