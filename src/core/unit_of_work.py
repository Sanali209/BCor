import abc
from collections.abc import Generator
from typing import Any

from src.core.domain import Aggregate
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

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any | None) -> None:  # noqa: ANN401
        """Finalizes the transaction."""
        self.rollback()

    async def __aenter__(self) -> "AbstractUnitOfWork":
        """Starts a new atomic transaction (async)."""
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any | None) -> None:  # noqa: ANN401
        """Finalizes the transaction (async)."""
        self.rollback()

    def commit(self) -> None:
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
    def _commit(self) -> None:
        """Concrete implementation for committing the transaction."""
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self) -> None:
        """Rolls back the active transaction."""
        raise NotImplementedError

    def _get_all_seen_aggregates(self) -> list[Aggregate]:
        """Finds all aggregates loaded in any repository within this UoW.

        Returns:
            A set of all aggregates currently tracked by this Unit of Work.
        """
        aggregates = set()
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, AbstractRepository):
                aggregates.update(attr.seen)
        return list(aggregates)
