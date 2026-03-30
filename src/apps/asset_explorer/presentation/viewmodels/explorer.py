from typing import Any, List, Optional, Type, Dict
from PySide6.QtCore import QObject, Signal, Slot
from src.modules.agm.mapper import AGMMapper
from neo4j import AsyncDriver
from src.modules.assets.domain.models import (
    Asset, ImageAsset, VideoAsset, AudioAsset, TextAsset, 
    PhysicalAsset, Tag, Product, Project
)
from src.modules.assets.domain.services import AssetIngestionService
from src.apps.asset_explorer.presentation.viewmodels.metadata import MetadataViewModel

class AssetExplorerViewModel(QObject):
    """
    Main ViewModel for the Asset Explorer View.
    Orchestrates search results (Middle Panel) and connects to Metadata (Right Panel).
    Supports 500-item batch pagination and metadata-driven search.
    """
    search_started = Signal()
    results_updated = Signal(list) # list[Asset]
    asset_selected = Signal(object) # current_asset
    operation_started = Signal(str) # name of operation
    operation_finished = Signal(str, bool) # name, success
    progress_updated = Signal(int, int, str) # current, total, status
    search_schema_updated = Signal(list) # list[dict]
    pagination_updated = Signal(int, bool, bool) # current_page, can_prev, can_next
    
    def __init__(self, mapper: AGMMapper, ingestion: AssetIngestionService, driver: AsyncDriver, parent=None):
        super().__init__(parent)
        self._mapper = mapper
        self._ingestion = ingestion
        self._driver = driver
        self._results: List[Asset] = []
        self._selected_asset: Optional[Asset] = None
        self._current_metadata: Optional[MetadataViewModel] = None
        
        # Pagination state
        self._current_offset = 0
        self._page_size = 500
        self._last_search_params: Dict[str, Any] = {}
        
        # Default models to explore/search
        self._active_models: List[Type] = [Asset, ImageAsset, VideoAsset, AudioAsset]
        self._search_schema: List[Dict[str, Any]] = []

    @property
    def results(self) -> List[Asset]:
        return self._results

    @property
    def selected_asset(self) -> Optional[Asset]:
        return self._selected_asset

    @property
    def current_metadata(self) -> Optional[MetadataViewModel]:
        return self._current_metadata

    @property
    def search_schema(self) -> List[Dict[str, Any]]:
        """Returns the dynamic search schema for active models."""
        if not self._search_schema:
            self.refresh_search_schema()
        return self._search_schema

    @property
    def current_page(self) -> int:
        return (self._current_offset // self._page_size) + 1

    def refresh_search_schema(self):
        """Discovers available search fields from active models."""
        if self._mapper.schema_manager:
            self._search_schema = self._mapper.schema_manager.get_search_schema(self._active_models)
            self.search_schema_updated.emit(self._search_schema)

    async def search(self, search_params: Optional[Dict[str, Any]] = None, offset: int = 0):
        """Perform a search using dynamic parameters and explicit pagination.
        
        Args:
            search_params: Dictionary of field names and values. If None, uses last params.
            offset: Number of items to skip for pagination.
        """
        self.search_started.emit()
        self._current_offset = offset
        if search_params is not None:
            self._last_search_params = search_params
        
        target_model = Asset
        
        async with self._driver.session() as session:
            query = self._mapper.query(target_model)
            
            for key, value in self._last_search_params.items():
                if value is None or value == "": continue
                
                # Retrieve field metadata to decide query type
                field_def = next((f for f in self.search_schema if f["name"] == key), None)
                if not field_def: continue
                
                if field_def["widget"] == "range" and isinstance(value, tuple):
                    query.range(key, value[0], value[1])
                elif field_def["widget"] == "date":
                    query.where(**{key: value})
                elif field_def["widget"] == "text":
                    query.contains(key, value)
                elif field_def["widget"] == "vector":
                    if isinstance(value, list):
                        query.near(key, value, limit=self._page_size)
                else:
                    query.where(**{key: value})
            
            # Apply explicit pagination
            query.skip(self._current_offset).limit(self._page_size)
            
            results = await query.all(session) 
        
        self._results = results
        self.results_updated.emit(self._results)
        
        # Update pagination state for UI
        can_prev = self._current_offset > 0
        can_next = len(results) == self._page_size # Heuristic for PoC
        self.pagination_updated.emit(self.current_page, can_prev, can_next)

    async def next_page(self):
        """Navigate to the next page of results."""
        await self.search(offset=self._current_offset + self._page_size)

    async def prev_page(self):
        """Navigate to the previous page of results."""
        await self.search(offset=max(0, self._current_offset - self._page_size))

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
        """Wipe all nodes from the graph database."""
        self.operation_started.emit("Clear Database")
        try:
            self._ingestion.stop_ingestion()
            async with self._driver.session() as session:
                await session.run("MATCH (n) DETACH DELETE n")
            self.operation_finished.emit("Clear Database", True)
            self._results = []
            self._current_offset = 0
            self.results_updated.emit(self._results)
            self.pagination_updated.emit(1, False, False)
            self.asset_selected.emit(None)
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to clear database: {e}")
            self.operation_finished.emit("Clear Database", False)

    async def mass_add(self, directory_path: str):
        """Crawl a directory and ingest assets."""
        self.operation_started.emit("Mass Add")
        async def on_progress(current, total, status):
            self.progress_updated.emit(current, total, status)
        try:
            async with self._driver.session() as session:
                await self._ingestion.ingest_directory(directory_path, session=session, progress_callback=on_progress)
            self.operation_finished.emit("Mass Add", True)
            await self.search({}, offset=0) # Refresh from start
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed mass add: {e}")
            self.operation_finished.emit("Mass Add", False)

    async def add_single_asset(self, file_path: str):
        """Add a single asset to the database."""
        self.operation_started.emit("Add Asset")
        self.progress_updated.emit(0, 1, f"Ingesting {file_path}...")
        try:
            async with self._driver.session() as session:
                asset = await self._ingestion.ingest_file(file_path, session=session)
            
            if asset:
                self.progress_updated.emit(1, 1, "Ingestion complete.")
                self.operation_finished.emit("Add Asset", True)
                await self.search({}, offset=0)  # Refresh view
            else:
                self.operation_finished.emit("Add Asset", False)
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to add single asset {file_path}: {e}")
            self.operation_finished.emit("Add Asset", False)
