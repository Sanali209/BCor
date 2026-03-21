from __future__ import annotations

from typing import Any

from ..infrastructure.sqlite_repo import SqliteImageRepo


class GetCollectionStatsUseCase:
    """Юзкейс для получения статистики коллекции."""

    def __init__(self, repo: SqliteImageRepo) -> None:
        self.repo = repo

    def execute(self) -> dict[str, Any]:
        return self.repo.get_stats()
