from __future__ import annotations

from dishka import Provider, Scope, provide

from src.core.module import BaseModule

from .adapters.processors.pil_processor import PILImageProcessor
from .domain.interfaces.image_processor import IImageProcessor
from .infrastructure.image_scanner import ImageScanner
from .infrastructure.sqlite_repo import SqliteImageRepo
from .use_cases import ExecuteBatchRulesUseCase, GetCollectionStatsUseCase, ScanDirectoryUseCase


class ImageAnalyzeProvider(Provider):
    @provide(scope=Scope.APP)
    def get_repo(self) -> SqliteImageRepo:
        # For now, use the default name in the current directory or config
        return SqliteImageRepo("astral_mariner.db")

    @provide(scope=Scope.APP)
    def get_scanner(self) -> ImageScanner:
        return ImageScanner()

    @provide(scope=Scope.APP)
    def get_processor(self) -> IImageProcessor:
        return PILImageProcessor()

    @provide(scope=Scope.REQUEST)
    def get_scan_use_case(self, repo: SqliteImageRepo, scanner: ImageScanner) -> ScanDirectoryUseCase:
        return ScanDirectoryUseCase(repo, scanner)

    @provide(scope=Scope.REQUEST)
    def get_stats_use_case(self, repo: SqliteImageRepo) -> GetCollectionStatsUseCase:
        return GetCollectionStatsUseCase(repo)

    @provide(scope=Scope.REQUEST)
    def get_batch_use_case(self, repo: SqliteImageRepo, processor: IImageProcessor) -> ExecuteBatchRulesUseCase:
        return ExecuteBatchRulesUseCase(repo, processor)

class ImageAnalyzeModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.provider = ImageAnalyzeProvider()
