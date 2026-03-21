import abc
from typing import Generic, TypeVar

from src.core.domain import Aggregate

T = TypeVar("T", bound=Aggregate)


class AbstractRepository(Generic[T], abc.ABC):  # noqa: UP046
    """Abstract base class for repositories.

    The Repository pattern abstracts the data storage layer, allowing the
    domain layer to remain independent of infrastructure concerns.
    Repositories should exclusively handle the persistence and retrieval
    of Aggregates.

    Attributes:
        seen: A set of aggregates loaded or added during the current session.
    """

    def __init__(self) -> None:
        """Initializes the repository with an empty 'seen' set."""
        self.seen: set[T] = set()

    def add(self, aggregate: T) -> None:
        """Adds a new aggregate to the repository and marks it as 'seen'.

        Args:
            aggregate: The aggregate instance to save.
        """
        self._add(aggregate)
        self.seen.add(aggregate)

    def get(self, reference: str) -> T | None:
        """Retrieves an aggregate by its unique reference and marks it as 'seen'.

        Args:
            reference: The unique identifier for the aggregate.

        Returns:
            The aggregate instance if found, otherwise None.
        """
        aggregate = self._get(reference)
        if aggregate:
            self.seen.add(aggregate)
        return aggregate

    @abc.abstractmethod
    def _add(self, aggregate: T) -> None:
        """Concrete implementation for adding an aggregate."""
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, reference: str) -> T | None:
        """Concrete implementation for retrieving an aggregate."""
        raise NotImplementedError
