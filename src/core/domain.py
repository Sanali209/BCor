from typing import List
from src.core.messages import Event


class Aggregate:
    """Base class for all domain aggregates.

    Aggregates form consistency boundaries and manage their own lifecycle
    and domain events. Events are collected here for later publishing 
    by the MessageBus via the Unit of Work.

    Attributes:
        events: A list of domain events that have occurred within this aggregate.
    """

    def __init__(self):
        """Initializes the aggregate with an empty event list."""
        self.events: List[Event] = []

    def add_event(self, event: Event) -> None:
        """Adds a new domain event to the aggregate.

        Args:
            event: The domain event instance to record.
        """
        self.events.append(event)
