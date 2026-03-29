"""ThumbnailHandler — Generates scaled thumbnails for assets and stores them in CAS."""
from __future__ import annotations

import pathlib
from typing import Any, Protocol, runtime_checkable

from PIL import Image
from loguru import logger

from src.core.storage import get_cas_path, ensure_cas_dir, SIZE_MAP


@runtime_checkable
class ThumbnailProvider(Protocol):
    """Protocol for specific asset thumbnail generators."""
    async def generate(self, path: pathlib.Path, content_hash: str, storage_root: str) -> bool:
        ...


class ImageThumbnailProvider:
    """Standard PIL-based provider for images."""
    
    async def generate(self, path: pathlib.Path, content_hash: str, storage_root: str) -> bool:
        try:
            with path.open("rb") as f:
                with Image.open(f) as img:
                    # Convert to RGB if needed (JPEG doesn't support RGBA/P)
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    
                    results = []
                    for size_name, target_size in SIZE_MAP.items():
                        cas_path = get_cas_path(storage_root, content_hash, size_name)
                        
                        if cas_path.exists():
                            results.append(True)
                            continue
                            
                        thumb = img.copy()
                        thumb.thumbnail(target_size)
                        
                        ensure_cas_dir(cas_path)
                        thumb.save(cas_path, format="JPEG", quality=85)
                        
                        logger.info(f"ThumbnailHandler [Image]: Saved {size_name} to {cas_path}")
                        results.append(True)
                    return any(results)
        except Exception as e:
            logger.error(f"ImageThumbnailProvider failed for {path}: {e}")
            return False


class ThumbnailHandler:
    """Polymorphic dispatcher for thumbnail generation.
    
    Dispatches to providers based on MIME type or extension.
    """
    
    PROVIDERS: dict[str, type[ThumbnailProvider]] = {
        "image/jpeg": ImageThumbnailProvider,
        "image/png": ImageThumbnailProvider,
        "image/webp": ImageThumbnailProvider,
        "image/gif": ImageThumbnailProvider,
        "image/bmp": ImageThumbnailProvider,
    }

    @classmethod
    async def run(cls, uri: str, context: dict[str, Any] | None = None) -> bool:
        """Main entry point for AGM.
        
        Args:
            uri: Asset URI.
            context: Context containing 'mime_type', 'storage_root', 'content_hash', etc.
        """
        content_hash = (context or {}).get("content_hash")
        if not content_hash:
            logger.warning(f"ThumbnailHandler: No content_hash for {uri}")
            return False

        mime_type = (context or {}).get("mime_type", "*/*").lower()
        storage_root = (context or {}).get("storage_root", "data")
        
        from src.core.storage import uri_to_path
        path = uri_to_path(uri)


        if not path.exists():
            logger.warning(f"ThumbnailHandler: File not found at {path}")
            return False

        # Find provider
        provider_cls = cls.PROVIDERS.get(mime_type)
        
        # Fallback by extension if mime_type is generic
        if not provider_cls:
            ext = path.suffix.lower()
            if ext in (".jpg", ".jpeg", ".png", ".webp"):
                provider_cls = ImageThumbnailProvider

        if not provider_cls:
            logger.debug(f"ThumbnailHandler: No provider for {mime_type} ({path.suffix}). Skipping.")
            return False

        provider = provider_cls()
        return await provider.generate(path, content_hash, storage_root)
