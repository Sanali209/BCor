"""
Thumbnail Cache Service Component using diskcache library.

Provides advanced thumbnail caching with multiple sizes, disk-based storage,
and comprehensive path conversion API as requested.
"""

import asyncio
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import diskcache

from loguru import logger
from PIL import Image

from SLM.core.component import Component
from .progress_service import ProgressService


class ThumbnailCacheService(Component):
    """
    Advanced thumbnail caching service using diskcache library.

    Features:
    - Multiple configurable thumbnail sizes
    - Disk-based caching with diskcache library
    - Path conversion API (full path ↔ thumbnail path)
    - Manual cache clearing (no auto-cleanup)
    - Progress tracking for cache operations
    - Memory-efficient thumbnail generation
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name or "thumbnail_cache_service")

        # Cache configuration
        self.cache_dir = "cache/thumbnails"
        self.supported_sizes = [64, 128, 256, 512, 1024]
        self.default_quality = 85
        self.thumbnail_format = "JPEG"

        # Cache instances for each size
        self.caches: Dict[int, diskcache.Cache] = {}
        self.path_conversions: Dict[str, Dict[int, str]] = {}

        # Statistics
        self.stats: Dict[str, Any] = {
            "cache_hits": 0,
            "cache_misses": 0,
            "thumbnails_generated": 0,
            "cache_size_mb": 0.0
        }

    async def on_initialize_async(self):
        """Initialize the thumbnail cache service."""
        # Initialize diskcache instances for each size
        for size in self.supported_sizes:
            size_dir = os.path.join(self.cache_dir, f"{size}x{size}")
            os.makedirs(size_dir, exist_ok=True)

            cache_path = os.path.join(size_dir, "cache.db")
            self.caches[size] = diskcache.Cache(cache_path)

        # Load existing path conversions
        await self._load_path_conversions()

        logger.info(f"Thumbnail cache service initialized with sizes: {self.supported_sizes}")

    async def on_start_async(self):
        """Start the thumbnail cache service."""
        # Update cache statistics
        await self._update_cache_stats()
        logger.info("Thumbnail cache service started")

    async def on_shutdown_async(self):
        """Shutdown the thumbnail cache service."""
        # Close all cache connections
        for cache in self.caches.values():
            cache.close()

        self.caches.clear()
        self.path_conversions.clear()

        logger.info("Thumbnail cache service shutdown")

    async def get_thumbnail_path(self, image_path: str, size: int) -> Optional[str]:
        """
        Get cached thumbnail path or create if not exists.

        Args:
            image_path: Path to the full-size image
            size: Desired thumbnail size in pixels

        Returns:
            Path to cached thumbnail or None if creation failed
        """
        # Validate size
        if size not in self.supported_sizes:
            logger.warning(f"Unsupported thumbnail size: {size}")
            return None

        # Check cache first
        cache_key = self._make_cache_key(image_path, size)

        if cache_key in self.caches[size]:
            self.stats["cache_hits"] += 1
            thumbnail_path = self.caches[size][cache_key]

            # Verify file still exists
            if os.path.exists(thumbnail_path):
                return thumbnail_path
            else:
                # Remove stale cache entry
                del self.caches[size][cache_key]
                if image_path in self.path_conversions and size in self.path_conversions[image_path]:
                    del self.path_conversions[image_path][size]

        # Cache miss - generate thumbnail
        self.stats["cache_misses"] += 1
        return await self._generate_thumbnail(image_path, size)

    async def create_thumbnail(self, image_path: str, size: int) -> Optional[str]:
        """
        Generate and cache a thumbnail.

        Args:
            image_path: Path to the full-size image
            size: Thumbnail size in pixels

        Returns:
            Path to created thumbnail or None if failed
        """
        return await self._generate_thumbnail(image_path, size)

    async def clear_cache(self, size: Optional[int] = None):
        """
        Clear cache for specific size or all sizes.

        Args:
            size: Size to clear (None for all sizes)
        """
        if size is None:
            # Clear all caches
            for cache in self.caches.values():
                cache.clear()

            self.path_conversions.clear()
            await self._save_path_conversions()

            logger.info("Cleared all thumbnail caches")
        else:
            # Clear specific size cache
            if size in self.caches:
                self.caches[size].clear()

                # Remove from path conversions
                await self._remove_size_from_conversions(size)

                logger.info(f"Cleared thumbnail cache for size {size}x{size}")

        # Update statistics
        await self._update_cache_stats()

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        await self._update_cache_stats()

        # Create new stats dictionary with proper typing
        stats = dict(self.stats)
        stats["supported_sizes"] = self.supported_sizes
        stats["cache_count_by_size"] = {
            size: getattr(cache, 'volume', lambda: 0)()
            for size, cache in self.caches.items()
        }
        stats["path_conversions_count"] = len(self.path_conversions)
        stats["cache_directory"] = self.cache_dir

        return stats

    async def preload_thumbnails(self, image_paths: List[str], sizes: Optional[List[int]] = None) -> str:
        """
        Preload thumbnails for multiple images.

        Args:
            image_paths: List of image paths to process
            sizes: Sizes to generate (uses all if None)

        Returns:
            Operation ID for progress tracking
        """
        if sizes is None:
            sizes = self.supported_sizes

        # Start progress tracking
        progress_service = None
        if hasattr(self, 'message_bus') and self.message_bus:
            # Try to get progress service
            try:
                progress_service = self.message_bus._dependency_manager.get_service(ProgressService)
            except:
                pass

        operation_id = None
        if progress_service:
            operation_id = await progress_service.start_operation(
                "preload_thumbnails",
                total_steps=len(image_paths) * len(sizes),
                metadata={"images": len(image_paths), "sizes": sizes}
            )

        # Process thumbnails
        completed = 0
        for image_path in image_paths:
            for size in sizes:
                try:
                    await self.get_thumbnail_path(image_path, size)
                    completed += 1

                    if operation_id and progress_service:
                        await progress_service.update_progress(
                            operation_id,
                            completed,
                            metadata={"current_image": image_path, "current_size": size}
                        )

                except Exception as e:
                    logger.error(f"Error preloading thumbnail {image_path}@{size}px: {e}")
                    completed += 1

                    if operation_id and progress_service:
                        await progress_service.update_progress(
                            operation_id,
                            completed,
                            metadata={"error": str(e)}
                        )

        if operation_id and progress_service:
            await progress_service.complete_operation(operation_id)

        return operation_id or "completed"

    def is_thumbnail_cached(self, image_path: str, size: int) -> bool:
        """
        Check if thumbnail exists in cache.

        Args:
            image_path: Path to the full-size image
            size: Thumbnail size to check

        Returns:
            True if thumbnail is cached
        """
        if size not in self.supported_sizes:
            return False

        cache_key = self._make_cache_key(image_path, size)
        return cache_key in self.caches[size]

    def get_available_sizes(self) -> List[int]:
        """
        Get list of available thumbnail sizes.

        Returns:
            List of supported thumbnail sizes
        """
        return self.supported_sizes.copy()

    def add_thumbnail_size(self, size: int) -> bool:
        """
        Add a new supported thumbnail size.

        Args:
            size: New size to add

        Returns:
            True if size was added successfully
        """
        if size in self.supported_sizes:
            return False

        if size < 16 or size > 2048:
            logger.warning(f"Thumbnail size {size} is outside recommended range (16-2048)")
            return False

        self.supported_sizes.append(size)
        self.supported_sizes.sort()

        # Create cache for new size
        size_dir = os.path.join(self.cache_dir, f"{size}x{size}")
        os.makedirs(size_dir, exist_ok=True)

        cache_path = os.path.join(size_dir, "cache.db")
        self.caches[size] = diskcache.Cache(cache_path)

        logger.info(f"Added thumbnail size: {size}x{size}")
        return True

    def remove_thumbnail_size(self, size: int) -> bool:
        """
        Remove a supported thumbnail size.

        Args:
            size: Size to remove

        Returns:
            True if size was removed successfully
        """
        if size not in self.supported_sizes:
            return False

        # Remove from supported sizes
        self.supported_sizes.remove(size)

        # Clear cache for this size
        if size in self.caches:
            self.caches[size].clear()
            self.caches[size].close()
            del self.caches[size]

        # Remove from path conversions
        import asyncio
        asyncio.create_task(self._remove_size_from_conversions(size))

        logger.info(f"Removed thumbnail size: {size}x{size}")
        return True

    async def _generate_thumbnail(self, image_path: str, size: int) -> Optional[str]:
        """
        Generate a thumbnail for an image.

        Args:
            image_path: Path to the source image
            size: Thumbnail size

        Returns:
            Path to generated thumbnail or None if failed
        """
        try:
            # Check if source image exists
            if not os.path.exists(image_path):
                logger.warning(f"Source image not found: {image_path}")
                return None

            # Open and process image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')

                # Calculate thumbnail size maintaining aspect ratio
                img.thumbnail((size, size), Image.Resampling.LANCZOS)

                # Generate output path
                cache_key = self._make_cache_key(image_path, size)
                thumbnail_path = self._get_thumbnail_path(image_path, size)

                # Ensure directory exists
                os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)

                # Save thumbnail
                img.save(thumbnail_path, self.thumbnail_format, quality=self.default_quality)

                # Cache the path mapping
                self.caches[size][cache_key] = thumbnail_path

                # Update path conversions
                if image_path not in self.path_conversions:
                    self.path_conversions[image_path] = {}
                self.path_conversions[image_path][size] = thumbnail_path

                # Save path conversions periodically
                await self._save_path_conversions()

                self.stats["thumbnails_generated"] += 1

                logger.debug(f"Generated thumbnail: {thumbnail_path}")
                return thumbnail_path

        except Exception as e:
            logger.error(f"Error generating thumbnail for {image_path}: {e}")
            return None

    def _make_cache_key(self, image_path: str, size: int) -> str:
        """
        Generate a cache key for an image and size.

        Args:
            image_path: Path to the image
            size: Thumbnail size

        Returns:
            Cache key string
        """
        # Use file path hash for consistent cache keys
        path_hash = hashlib.md5(image_path.encode()).hexdigest()[:16]
        return f"{path_hash}_{size}"

    def _get_thumbnail_path(self, image_path: str, size: int) -> str:
        """
        Generate thumbnail file path.

        Args:
            image_path: Path to the source image
            size: Thumbnail size

        Returns:
            Thumbnail file path
        """
        # Use file hash for unique filename
        file_hash = hashlib.md5(image_path.encode()).hexdigest()[:16]
        filename = f"{file_hash}.jpg"

        size_dir = os.path.join(self.cache_dir, f"{size}x{size}")
        return os.path.join(size_dir, filename)

    async def _load_path_conversions(self):
        """Load path conversion mappings from disk."""
        conversions_file = os.path.join(self.cache_dir, "path_conversions.json")

        try:
            if os.path.exists(conversions_file):
                import json
                with open(conversions_file, 'r', encoding='utf-8') as f:
                    self.path_conversions = json.load(f)
                logger.debug("Loaded path conversions from disk")
        except Exception as e:
            logger.warning(f"Could not load path conversions: {e}")
            self.path_conversions = {}

    async def _save_path_conversions(self):
        """Save path conversion mappings to disk."""
        conversions_file = os.path.join(self.cache_dir, "path_conversions.json")

        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            import json
            with open(conversions_file, 'w', encoding='utf-8') as f:
                json.dump(self.path_conversions, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save path conversions: {e}")

    async def _remove_size_from_conversions(self, size: int):
        """Remove all path conversions for a specific size."""
        for image_path in self.path_conversions:
            if size in self.path_conversions[image_path]:
                del self.path_conversions[image_path][size]

        await self._save_path_conversions()

    async def _update_cache_stats(self):
        """Update cache statistics."""
        total_size = 0

        for size, cache in self.caches.items():
            # Count entries
            try:
                cache_size = len(cache)
                # Estimate size (rough calculation)
                size_dir = os.path.join(self.cache_dir, f"{size}x{size}")
                if os.path.exists(size_dir):
                    dir_size = sum(
                        os.path.getsize(os.path.join(size_dir, f))
                        for f in os.listdir(size_dir)
                        if os.path.isfile(os.path.join(size_dir, f))
                    )
                    total_size += dir_size
            except Exception as e:
                logger.warning(f"Error calculating cache size for {size}x{size}: {e}")

        self.stats["cache_size_mb"] = total_size / (1024 * 1024)

    def get_path_conversions(self) -> Dict[str, Dict[int, str]]:
        """
        Get all path conversion mappings.

        Returns:
            Dictionary of image_path -> {size: thumbnail_path}
        """
        return self.path_conversions.copy()

    def cleanup_invalid_entries(self):
        """
        Remove cache entries for non-existent files.
        """
        import asyncio
        asyncio.create_task(self._cleanup_invalid_entries_async())

    async def _cleanup_invalid_entries_async(self):
        """
        Async version of cleanup for invalid cache entries.
        """
        operation_id = None

        # Try to get progress service
        progress_service = None
        if hasattr(self, 'message_bus') and self.message_bus:
            try:
                progress_service = self.message_bus._dependency_manager.get_service(ProgressService)
            except:
                pass

        if progress_service:
            operation_id = await progress_service.start_operation(
                "cleanup_invalid_cache_entries",
                total_steps=len(self.path_conversions),
                metadata={"total_images": len(self.path_conversions)}
            )

        removed_count = 0
        for image_path, size_map in list(self.path_conversions.items()):
            if not os.path.exists(image_path):
                # Remove all thumbnails for this image
                for size, thumbnail_path in size_map.items():
                    if size in self.caches and os.path.exists(thumbnail_path):
                        try:
                            os.remove(thumbnail_path)
                        except Exception as e:
                            logger.warning(f"Could not remove thumbnail {thumbnail_path}: {e}")

                    # Remove from cache
                    if size in self.caches:
                        cache_key = self._make_cache_key(image_path, size)
                        if cache_key in self.caches[size]:
                            del self.caches[size][cache_key]

                # Remove from path conversions
                del self.path_conversions[image_path]
                removed_count += 1

            if operation_id and progress_service:
                completed = removed_count
                await progress_service.update_progress(
                    operation_id,
                    completed,
                    metadata={"removed_count": removed_count}
                )

        if operation_id and progress_service:
            await progress_service.complete_operation(operation_id)

        if removed_count > 0:
            await self._save_path_conversions()
            logger.info(f"Cleaned up {removed_count} invalid cache entries")

        # Update statistics
        await self._update_cache_stats()
