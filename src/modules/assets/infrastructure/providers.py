"""DI providers for the Assets module infrastructure."""
from __future__ import annotations

from dishka import Provider, Scope, provide

from src.modules.assets.infrastructure.registry import HandlerRegistry
from src.modules.assets.infrastructure.handlers.phash import PHashHandler
from src.modules.assets.infrastructure.handlers.clip import CLIPHandler
from src.modules.assets.infrastructure.handlers.blip import BLIPHandler
from src.modules.assets.infrastructure.handlers.pyexiv2 import Pyexiv2Handler
from src.modules.assets.infrastructure.handlers.ollama import OllamaHandler
from src.modules.assets.infrastructure.handlers.smart_exif import Pyexiv2SmartHandler


class AssetsInfrastructureProvider(Provider):
    """Provides Assets-related infrastructure dependencies."""

    scope = Scope.APP

    @provide
    def provide_handler_registry(self) -> HandlerRegistry:
        """Provides a singleton HandlerRegistry with registered image handlers."""
        from src.modules.assets.infrastructure.handlers.thumbnail import ThumbnailHandler
        from src.modules.assets.infrastructure.handlers.ocr import EasyOCRHandler
        from src.modules.assets.domain.services import TagMerger
        from src.modules.assets.infrastructure.dedup import SemanticDuplicateFinder
        from src.modules.assets.infrastructure.handlers.smilingwolf import SmilingWolfHandler

        registry = HandlerRegistry()
        
        # 1. Registered by MIME category fallback
        registry.register("image/*", ThumbnailHandler)
        registry.register("*/*", ThumbnailHandler)  # Generic fallback for thumbnails
        
        # 2. Registered by explicit name for @Stored(handler="...")
        registry.register_named("PHash", PHashHandler)
        registry.register_named("PHashHandler", PHashHandler)
        registry.register_named("CLIP", CLIPHandler)
        registry.register_named("CLIPHandler", CLIPHandler)
        registry.register_named("BLIP", BLIPHandler)
        registry.register_named("BLIPHandler", BLIPHandler)
        registry.register_named("Pyexiv2", Pyexiv2Handler)
        registry.register_named("Pyexiv2_Write", Pyexiv2Handler)  # Reuses same class
        registry.register_named("Pyexiv2Smart", Pyexiv2SmartHandler)
        from src.modules.assets.infrastructure.handlers.base_hash import ContentHashHandler
        registry.register_named("ContentHashHandler", ContentHashHandler)
        registry.register_named("content_hash", ContentHashHandler)
        registry.register_named("ThumbnailHandler", ThumbnailHandler)
        registry.register_named("thumbnails_ready", ThumbnailHandler)
        registry.register_named("EasyOCR", EasyOCRHandler)
        registry.register_named("TagMerger", TagMerger)
        registry.register_named("SemanticDuplicateFinder", SemanticDuplicateFinder)
        registry.register_named("OllamaVLM", OllamaHandler)
        registry.register_named("OllamaEmbedding", OllamaHandler)
        registry.register_named("SmilingWolfHandler", SmilingWolfHandler)
        registry.register_named("wd_tags", SmilingWolfHandler)
        registry.register_named("blip_caption", BLIPHandler)
        registry.register_named("clip_embedding", CLIPHandler)
        registry.register_named("exif_data", Pyexiv2SmartHandler)
        
        return registry
