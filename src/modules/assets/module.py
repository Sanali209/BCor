"""Assets module definition for BCor."""
from __future__ import annotations
from loguru import logger

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
        """Called during bootstrap."""
        pass

    async def startup(self) -> None:
        """Register domain models with AGMMapper after the container is ready."""
        from src.modules.agm.mapper import AGMMapper
        from src.modules.assets.domain.models import (
            Asset, ImageAsset, VideoAsset, AudioAsset, TextAsset, 
            PhysicalAsset, Tag, Product, Project, InferenceEvent
        )
        
        # Modules are guaranteed to have a container by the System before startup
        mapper = await self.container.get(AGMMapper)
        
        # Register all core models to trigger schema sync and polymorphism
        models = [
            Asset, ImageAsset, VideoAsset, AudioAsset, TextAsset,
            PhysicalAsset, Tag, Product, Project, InferenceEvent
        ]
        
        for model in models:
            await mapper.register_subclass(model.__name__, model)
        
        logger.info(f"AssetsModule: Registered {len(models)} domain models with AGMMapper.")
