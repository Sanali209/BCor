"""Assets module definition for BCor."""
from __future__ import annotations

from src.core.module import BaseModule
from src.modules.assets.infrastructure.providers import AssetsInfrastructureProvider


class AssetsModule(BaseModule):
    """Module for managing digital and physical assets.
    
    Provides declarative models, metadata-driven persistence (AGM),
    and automated field processing (embeddings, hashes, thumbnails).
    """

    def __init__(self) -> None:
        """Initializes the Assets module and its infrastructure provider."""
        super().__init__()
        self.provider = AssetsInfrastructureProvider()

    async def setup(self) -> None:
        """Register domain models with AGMMapper for automated schema management."""
        from src.modules.agm.mapper import AGMMapper
        from src.modules.assets.domain.models import (
            Asset, ImageAsset, VideoAsset, AudioAsset, TextAsset, 
            PhysicalAsset, Tag, Product, Project, InferenceEvent
        )
        
        # In BCor system lifecycle, modules are initialized with the container
        if not hasattr(self, "container") or not self.container:
            return

        mapper = await self.container.get(AGMMapper)
        
        # Register all core models to trigger schema sync (indexes, unique constraints)
        models = [
            Asset, ImageAsset, VideoAsset, AudioAsset, TextAsset,
            PhysicalAsset, Tag, Product, Project, InferenceEvent
        ]
        
        for model in models:
            await mapper.register_subclass(model.__name__, model)
