from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from dishka import Provider, Scope, provide

from src.apps.asset_explorer.presentation.viewmodels.explorer import AssetExplorerViewModel
from src.apps.asset_explorer.presentation.viewmodels.metadata import MetadataViewModel
from src.modules.agm.mapper import AGMMapper
from src.modules.assets.domain.factory import AssetFactory
from src.modules.assets.domain.services import AssetIngestionService
from src.core.unit_of_work import AbstractUnitOfWork

class StubUnitOfWork(AbstractUnitOfWork):
    """No-op Unit of Work to satisfy dependencies for read-only / direct-access apps."""
    def _commit(self) -> None: pass
    def rollback(self) -> None: pass

class AssetExplorerProvider(Provider):
    """Dishka Provider for Asset Explorer components."""

    # Scope is now APP for shared driver, REQUEST for session-specific things
    # but we'll use property overrides if needed.
    
    @provide(scope=Scope.APP)
    def provide_neo_driver(self) -> AsyncDriver:
        # Default credentials for local BCor environment
        uri = "bolt://localhost:7687"
        auth = ("neo4j", "password")
        return AsyncGraphDatabase.driver(uri, auth=auth)

    @provide(scope=Scope.REQUEST)
    def provide_neo_session(self, driver: AsyncDriver) -> AsyncSession:
        return driver.session()

    @provide(scope=Scope.APP)
    def provide_asset_factory(self) -> AssetFactory:
        return AssetFactory()

    @provide(scope=Scope.REQUEST)
    def provide_ingestion_service(self, mapper: AGMMapper, factory: AssetFactory) -> AssetIngestionService:
        return AssetIngestionService(mapper=mapper, factory=factory)

    @provide(scope=Scope.APP)
    def provide_uow(self) -> AbstractUnitOfWork:
        """Provides a StubUnitOfWork to satisfy message bus requirements."""
        return StubUnitOfWork()

    @provide(scope=Scope.REQUEST)
    def provide_explorer_vm(self, mapper: AGMMapper, ingestion: AssetIngestionService, driver: AsyncDriver) -> AssetExplorerViewModel:
        return AssetExplorerViewModel(mapper=mapper, ingestion=ingestion, driver=driver)

    @provide(scope=Scope.REQUEST)
    def provide_metadata_vm(self, mapper: AGMMapper) -> MetadataViewModel:
        # MetadataViewModel will handle an asset dynamically, but could benefit from mapper for saving
        # For now, it might be instantiated per-selection in the UI.
        return MetadataViewModel()
