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
