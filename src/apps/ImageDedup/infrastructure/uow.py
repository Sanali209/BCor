from __future__ import annotations

from src.core.domain import Aggregate
from src.core.unit_of_work import AbstractUnitOfWork

from .repositories import JsonProjectRepository


class ImageDedupUnitOfWork(AbstractUnitOfWork):
    """Async-compatible Unit of Work for ImageDedup."""

    def __init__(self, work_path: str = ".") -> None:
        self.projects = JsonProjectRepository(work_path)

    async def __aenter__(self) -> ImageDedupUnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        if exc_type:
            self.rollback()
        # Note: commit() is called explicitly in handlers currently

    def _commit(self) -> None:
        """No-op for JSON; save is explicit in repository or called here if needed."""
        pass

    def rollback(self) -> None:
        """No-op for JSON side effects."""
        pass

    def _get_all_seen_aggregates(self) -> list[Aggregate]:
        # Cast projects.seen to list of Aggregate to satisfy base class
        return list(self.projects.seen)
