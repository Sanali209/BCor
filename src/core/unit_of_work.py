import abc
from typing import Generator

from src.core.messages import Event
from src.core.repository import AbstractRepository


class AbstractUnitOfWork(abc.ABC):
    """Abstract base class for Unit of Work.

    Provides atomic transactions and domain event collection.
    """

    # Repositories should be explicitly defined by the subclass
    # for instance:
    # my_repo: AbstractRepository[MyAggregate]

    def __enter__(self) -> "AbstractUnitOfWork":
        """Enter the context manager, starting a transaction."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager.

        If an exception is raised (exc_type is not None), rolls back the transaction.
        Otherwise, we do NOT commit automatically. The developer must call commit().
        But we do rollback implicitly for safety if they didn't commit explicitly.
        """
        self.rollback()

    def commit(self):
        """Commit the transaction and flush changes to the database."""
        self._commit()

    def collect_new_events(self) -> Generator[Event, None, None]:
        """Collect unhandled events from all loaded aggregates."""
        for aggregate in self._get_all_seen_aggregates():
            while aggregate.events:
                yield aggregate.events.pop(0)

    @abc.abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        """Rollback the active transaction."""
        raise NotImplementedError

    def _get_all_seen_aggregates(self):
        """Retrieve aggregates from all configured repositories in this UoW."""
        aggregates = set()
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, AbstractRepository):
                aggregates.update(attr.seen)
        return aggregates
