from typing import Any, Dict, List, Optional
from uuid import UUID

from src.core.module import BaseModule
from src.core.system import Provider, Scope, provide

from .application.commands import (
    UploadImage, UpdateImageMetadata, AssignCategories, CreateRelation, RunAiScan
)
from .application.handlers import (
    handle_upload_image, handle_update_metadata, handle_assign_categories
)
from .application.uow import GalleryUnitOfWork
from .infrastructure.models import start_mappers
from .infrastructure.chroma_adapter import ChromaAdapter
from .infrastructure.vector_repository import ChromaVectorRepository


class GalleryProvider(Provider):
    """Dishka Provider for the Gallery module."""

    @provide(scope=Scope.APP)
    def provide_chroma_adapter(self) -> ChromaAdapter:
        return ChromaAdapter(path="./data/chroma_db")

    @provide(scope=Scope.APP)
    def provide_vector_repository(self, adapter: ChromaAdapter) -> ChromaVectorRepository:
        return ChromaVectorRepository(adapter)

    @provide(scope=Scope.REQUEST)
    def provide_gallery_uow(self, session_factory: Any) -> GalleryUnitOfWork:
        # Note: session_factory is provided by the core database module
        return GalleryUnitOfWork(session_factory)


class GalleryModule(BaseModule):
    """BCor Module for Gallery management."""

    def __init__(self) -> None:
        super().__init__()
        self.provider = GalleryProvider()

    def setup(self) -> None:
        """Register command and event handlers."""
        # Config SQLAlchemy mappings
        start_mappers()

        # Command mapping
        self.command_handlers = {
            UploadImage: handle_upload_image,
            UpdateImageMetadata: handle_update_metadata,
            AssignCategories: handle_assign_categories,
        }

        # Event mapping
        self.event_handlers = {}
