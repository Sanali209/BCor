import abc
from typing import Generator

from src.core.messages import Event
from src.core.repository import AbstractRepository


class AbstractUnitOfWork(abc.ABC):
    """Abstract base class for the Unit of Work pattern.
    
    The Unit of Work coordinates the writing of changes and the 
    dispatching of events. It ensures that all operations within a 
    business transaction are atomic and that domain events are 
    collected for later publishing.
    """

    def __enter__(self) -> "AbstractUnitOfWork":
        """Starts a new atomic transaction.

        Returns:
            The Unit of Work instance.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finalizes the transaction.

        If an exception occurred, the transaction is rolled back. 
        Note that commit() must be called explicitly for success; 
        otherwise, a rollback is performed for safety.

        Args:
            exc_type: The type of exception raised, if any.
            exc_val: The exception instance, if any.
            exc_tb: The traceback, if any.
        """
        self.rollback()

    def commit(self):
        """Commits the active transaction to the database."""
        self._commit()

    def collect_new_events(self) -> Generator[Event, None, None]:
        """Collects all pending domain events from 'seen' aggregates.

        Yields:
            Domain events that have been added to aggregates during the transaction.
        """
        for aggregate in self._get_all_seen_aggregates():
            while aggregate.events:
                yield aggregate.events.pop(0)

    @abc.abstractmethod
    def _commit(self):
        """Concrete implementation for committing the transaction."""
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        """Rolls back the active transaction."""
        raise NotImplementedError

    def _get_all_seen_aggregates(self):
        """Finds all aggregates loaded in any repository within this UoW.

        Returns:
            A set of all aggregates currently tracked by this Unit of Work.
        """
        aggregates = set()
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, AbstractRepository):
                aggregates.update(attr.seen)
        return aggregates
