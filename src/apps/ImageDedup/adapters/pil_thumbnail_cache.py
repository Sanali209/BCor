from __future__ import annotations

from collections import OrderedDict
from typing import Any

from PIL import Image

from src.apps.ImageDedup.domain.interfaces.i_image_differ import IThumbnailCache


class PILThumbnailCache(IThumbnailCache):
    """Memory-efficient thumbnail cache using PIL."""

    def __init__(self, max_items: int = 500, default_size: tuple[int, int] = (300, 300)) -> None:
        self.max_items = max_items
        self.default_size = default_size
        self._cache: OrderedDict[str, Any] = OrderedDict()

    def get_thumbnail(self, path: str, max_size: tuple[int, int] | None = (300, 300)) -> object:
        """Retrieves or creates a thumbnail image.
        
        If not in cache, loads it, resizes, and stores.
        """
        size = max_size or self.default_size
        cache_key = f"{path}_{size[0]}x{size[1]}"

        if cache_key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        try:
            with Image.open(path) as img:
                img.thumbnail(size)
                # We convert to BGR for potential CV2 usage or keep as PIL for UI conversion
                thumbnail = img.copy()
            
            self._cache[cache_key] = thumbnail
            
            # Evict if full
            if len(self._cache) > self.max_items:
                self._cache.popitem(last=False)
                
            return thumbnail
        except Exception:
            # Return a small placeholder on error
            placeholder = Image.new("RGB", (32, 32), (200, 200, 200))
            return placeholder

    def clear(self) -> None:
        """Manually clear the cache."""
        self._cache.clear()
