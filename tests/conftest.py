from typing import Dict, Optional
from src.core.repository import AbstractRepository
from src.core.unit_of_work import AbstractUnitOfWork
from src.core.domain import Aggregate


class FakeAggregate(Aggregate):
    """A fake aggregate used for testing purposes."""

    def __init__(self, ref: str):
        super().__init__()
        self.ref = ref
        self.version = 1


class FakeRepository(AbstractRepository[FakeAggregate]):
    """An in-memory fake repository for testing."""

    def __init__(self):
        super().__init__()
        self._aggregates: Dict[str, FakeAggregate] = {}

    def _add(self, aggregate: FakeAggregate) -> None:
        self._aggregates[aggregate.ref] = aggregate

    def _get(self, reference: str) -> Optional[FakeAggregate]:
        return self._aggregates.get(reference)


class FakeUnitOfWork(AbstractUnitOfWork):
    """An in-memory fake UoW for testing."""

    def __init__(self):
        self.repo = FakeRepository()
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        self.committed = False
        self.rolled_back = False
        return super().__enter__()

    def _commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True
