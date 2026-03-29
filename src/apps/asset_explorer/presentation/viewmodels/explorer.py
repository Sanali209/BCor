from typing import Any, List, Optional
from PySide6.QtCore import QObject, Signal, Slot
from src.modules.agm.mapper import AGMMapper
from neo4j import AsyncDriver
from src.modules.assets.domain.models import Asset
from src.modules.assets.domain.services import AssetIngestionService
from src.apps.asset_explorer.presentation.viewmodels.metadata import MetadataViewModel

class AssetExplorerViewModel(QObject):
    """
    Main ViewModel for the Asset Explorer View.
    Orchestrates search results (Middle Panel) and connects to Metadata (Right Panel).
    """
    search_started = Signal()
    results_updated = Signal(list) # list[Asset]
    asset_selected = Signal(object) # current_asset
    operation_started = Signal(str) # name of operation
    operation_finished = Signal(str, bool) # name, success
    
    def __init__(self, mapper: AGMMapper, ingestion: AssetIngestionService, driver: AsyncDriver, parent=None):
        super().__init__(parent)
        self._mapper = mapper
        self._ingestion = ingestion
        self._driver = driver
        self._results: List[Asset] = []
        self._selected_asset: Optional[Asset] = None
        self._current_metadata: Optional[MetadataViewModel] = None

    @property
    def results(self) -> List[Asset]:
        return self._results

    @property
    def selected_asset(self) -> Optional[Asset]:
        return self._selected_asset

    @property
    def current_metadata(self) -> Optional[MetadataViewModel]:
        return self._current_metadata

    async def search(self, query_text: str = ""):
        """Perform a search via AGMMapper. Addresses search placeholder in previous sessions."""
        self.search_started.emit()
        
        async with self._driver.session() as session:
            query = self._mapper.query(Asset)
            if query_text:
                # Basic exact match for now, or fallback filtering if query builder is limited
                # Note: CypherQuery.where() supports exact prop match
                if ":" in query_text:
                    k, v = query_text.split(":", 1)
                    query.where(**{k.strip(): v.strip()})
                else:
                    # In-memory filter fallback for name if query builder lacks CONTAINS
                    all_assets = await query.all(session)
                    results = [a for a in all_assets if query_text.lower() in (a.name or "").lower()]
                
                if "results" not in locals():
                    results = await query.all(session)
            else:
                results = await query.all(session) 
        
        self._results = results
        self.results_updated.emit(self._results)

    @Slot(str)
    def select_asset(self, asset_id: str):
        """Set the current selected asset by ID."""
        target = next((a for a in self._results if a.id == asset_id), None)
        if target:
            self._selected_asset = target
            self._current_metadata = MetadataViewModel(target, mapper=self._mapper, parent=self)
            self.asset_selected.emit(target)
        else:
            self._selected_asset = None
            self._current_metadata = None
            self.asset_selected.emit(None)

    async def clear_database(self):
        """Wipe all nodes from the graph database and stop current ingestion."""
        self.operation_started.emit("Clear Database")
        try:
            # 1. Stop current crawler if running
            self._ingestion.stop_ingestion()

            # 2. Deep Wipe (All Nodes)
            async with self._driver.session() as session:
                await session.run("MATCH (n) DETACH DELETE n")

            self.operation_finished.emit("Clear Database", True)
            self._results = []
            self.results_updated.emit(self._results)
            self.asset_selected.emit(None)
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to clear database: {e}")
            self.operation_finished.emit("Clear Database", False)

    async def mass_add(self, directory_path: str):
        """Crawl a directory and ingest discovered assets into the graph."""
        self.operation_started.emit("Mass Add")
        try:
            # Ingest assets using the provided domain service
            async with self._driver.session() as session:
                await self._ingestion.ingest_directory(directory_path, session=session)
            self.operation_finished.emit("Mass Add", True)
            await self.search("") # Refresh results
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed mass add from {directory_path}: {e}")
            self.operation_finished.emit("Mass Add", False)
