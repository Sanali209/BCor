from __future__ import annotations

from dishka import Provider, Scope, provide
from src.core.module import BaseModule
from src.core.unit_of_work import AbstractUnitOfWork


# Import legacy components from this app
from .core.database import DatabaseManager
from .core.repositories.file_repository import FileRepository
from .core.repositories.cluster_repository import ClusterRepository
from .core.scan_session import ScanSession
from .use_cases.load_project import LoadProjectUseCase

import typing

class ImageDedupProvider(Provider):

    @provide(scope=Scope.APP)
    def get_db_manager(self) -> typing.Iterable[DatabaseManager]:
        db = DatabaseManager()
        yield db
        db.close()

    @provide(scope=Scope.APP)
    def get_file_repo(self, db: DatabaseManager) -> FileRepository:
        return FileRepository(db)

    @provide(scope=Scope.APP)
    def get_cluster_repo(self, db: DatabaseManager) -> ClusterRepository:
        return ClusterRepository(db)

    @provide(scope=Scope.APP)
    def get_scan_session(self, file_repo: FileRepository) -> ScanSession:
        return ScanSession(file_repo)

    @provide(scope=Scope.REQUEST)
    def get_uow(self) -> AbstractUnitOfWork:
        from .infrastructure.uow import ImageDedupUnitOfWork
        return ImageDedupUnitOfWork()

    @provide(scope=Scope.REQUEST)
    def get_load_project_use_case(self, file_repo: FileRepository) -> LoadProjectUseCase:

        return LoadProjectUseCase(file_repo)



class ImageDedupModule(BaseModule):
    def __init__(self) -> None:
        super().__init__()
        self.provider = ImageDedupProvider()
        
    def setup(self) -> None:
        """Map command handlers."""
        from .handlers import launch_gui_handler, load_project_handler
        from .messages import LaunchGuiCommand, LoadProjectCommand
        
        self.command_handlers = {
            LaunchGuiCommand: launch_gui_handler,
            LoadProjectCommand: load_project_handler,
        }

