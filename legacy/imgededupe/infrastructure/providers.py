from dishka import Provider, Scope, provide, from_context
from src.core.unit_of_work import AbstractUnitOfWork
from src.apps.experemental.imgededupe.core.database import DatabaseManager
from src.apps.experemental.imgededupe.core.unit_of_work import SqliteUnitOfWork
from src.apps.experemental.imgededupe.core.repositories.file_repository import FileRepository
from src.apps.experemental.imgededupe.core.repositories.cluster_repository import ClusterRepository
from pydantic_settings import BaseSettings
from src.apps.experemental.imgededupe.core.deduper import Deduper
from src.apps.experemental.imgededupe.core.scanner import Scanner
from src.apps.experemental.imgededupe.ui.adapter import GuiEventAdapter
from src.apps.experemental.imgededupe.core.scan_session import ScanSession
from src.apps.experemental.imgededupe.settings import ImgeDeduplicationSettings

class ImgeDeduplicationProvider(Provider):
    """
    Dishka Provider for imgededupe components.
    Bridges legacy services into the BCor DI container.
    """
    @provide(scope=Scope.APP)
    def provide_settings(self, settings: dict[str, BaseSettings]) -> ImgeDeduplicationSettings:
        return settings["imgededuplication"]
    @provide(scope=Scope.APP)
    def provide_db_manager(self, settings: "ImgeDeduplicationSettings") -> DatabaseManager:
        return DatabaseManager(settings.db_path)

    @provide(scope=Scope.APP)
    def provide_file_repository(self, db: DatabaseManager) -> FileRepository:
        return FileRepository(db)

    @provide(scope=Scope.APP)
    def provide_cluster_repository(self, db: DatabaseManager) -> ClusterRepository:
        return ClusterRepository(db)

    @provide(scope=Scope.APP)
    def provide_uow(self, db: DatabaseManager) -> AbstractUnitOfWork:
        return SqliteUnitOfWork(db)

    @provide(scope=Scope.APP)
    def provide_deduper(self, db_manager: DatabaseManager, file_repo: FileRepository) -> Deduper:
        return Deduper(db_manager, file_repo)

    @provide(scope=Scope.APP)
    def provide_scanner(self, db: DatabaseManager, deduper: Deduper) -> Scanner:
        return Scanner(db, deduper)

    @provide(scope=Scope.APP)
    def provide_scan_session(self, file_repo: FileRepository) -> ScanSession:
        return ScanSession(file_repo)

    @provide(scope=Scope.APP)
    def provide_gui_adapter(self) -> GuiEventAdapter:
        return GuiEventAdapter()
