from typing import List
from src.core.messages import Event


class Aggregate:
    """Base class for all aggregates.

    Aggregates form consistency boundaries and manage domain events.
    """

    def __init__(self):
        self.events: List[Event] = []

    def add_event(self, event: Event) -> None:
        """Add a new domain event to the aggregate."""
        self.events.append(event)
