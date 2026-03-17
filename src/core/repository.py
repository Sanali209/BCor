import abc
from typing import TypeVar, Generic, Set, Optional

from src.core.domain import Aggregate

T = TypeVar("T", bound=Aggregate)


class AbstractRepository(Generic[T], abc.ABC):
    """Abstract base class for repositories.

    Repositories should only save and load Aggregates.
    """

    def __init__(self):
        self.seen: Set[T] = set()

    def add(self, aggregate: T) -> None:
        """Add a new aggregate to the repository."""
        self._add(aggregate)
        self.seen.add(aggregate)

    def get(self, reference: str) -> Optional[T]:
        """Get an aggregate from the repository by reference."""
        aggregate = self._get(reference)
        if aggregate:
            self.seen.add(aggregate)
        return aggregate

    @abc.abstractmethod
    def _add(self, aggregate: T) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, reference: str) -> Optional[T]:
        raise NotImplementedError
