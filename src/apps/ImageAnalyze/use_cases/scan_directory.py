from __future__ import annotations

from collections.abc import Awaitable, Callable

from ..domain.models import ImageAnalysisRecord
from ..infrastructure.image_scanner import ImageScanner
from ..infrastructure.sqlite_repo import SqliteImageRepo


class ScanDirectoryUseCase:
    """Юзкейс для сканирования директории.
    Координирует работу сканера и сохраняет результаты в репозиторий.
    """

    def __init__(self, repo: SqliteImageRepo, scanner: ImageScanner) -> None:
        self.repo = repo
        self.scanner = scanner

    async def execute(
        self, directory_path: str, progress_callback: Callable[[int, int, str], Awaitable[None]] | None = None
    ) -> int:
        # 1. Clear existing generic data if requested?
        # Legacy cleared on every fresh scan. We follow.
        self.repo.clear()

        # 2. Scan
        records = await self.scanner.scan_directory(directory_path, progress_callback)

        # 3. Store
        self.repo.bulk_insert(records)

        return len(records)
