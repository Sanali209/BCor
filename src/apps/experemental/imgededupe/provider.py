from dishka import Provider, Scope, provide
from src.core.unit_of_work import AbstractUnitOfWork
from src.apps.experemental.imgededupe.core.database import DatabaseManager
from src.apps.experemental.imgededupe.core.unit_of_work import SqliteUnitOfWork
from src.apps.experemental.imgededupe.core.repositories.file_repository import FileRepository
from src.apps.experemental.imgededupe.core.repositories.cluster_repository import ClusterRepository
from src.apps.experemental.imgededupe.core.deduper import Deduper

class ImgeDeduplicationProvider(Provider):
    """
    Dishka Provider for imgededupe components.
    Bridges legacy services into the BCor DI container.
    """
    @provide(scope=Scope.APP)
    def provide_db_manager(self) -> DatabaseManager:
        return DatabaseManager("imgededupe.db")

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
    def provide_deduper(self, file_repo: FileRepository, cluster_repo: ClusterRepository) -> Deduper:
        return Deduper(file_repo, cluster_repo)
