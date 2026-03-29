"""
Image Download Service Component for async image downloading.

Provides async image downloading with progress tracking, error handling,
and integration with the thumbnail caching system.
"""

import asyncio
import os
import aiohttp
import aiofiles
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from loguru import logger

from SLM.core.component import Component
from .progress_service import ProgressService
from .thumbnail_cache_service import ThumbnailCacheService


@dataclass
class DownloadResult:
    """Represents the result of an image download operation."""

    url: str
    local_path: str
    success: bool
    file_size: int = 0
    error_message: str = ""
    download_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "url": self.url,
            "local_path": self.local_path,
            "success": self.success,
            "file_size": self.file_size,
            "error_message": self.error_message,
            "download_time": self.download_time
        }


class ImageDownloadService(Component):
    """
    Async image download service with SLM integration.

    Features:
    - Async image downloading with aiohttp
    - Progress tracking for download operations
    - Error handling and retry logic
    - Integration with thumbnail caching
    - Concurrent download limits
    - Download history and statistics
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name or "image_download_service")

        # Download configuration
        self.concurrent_downloads = 5
        self.timeout = 30
        self.retry_attempts = 3
        self.retry_delay = 1.0
        self.chunk_size = 8192

        # Download tracking
        self.download_history: List[DownloadResult] = []
        self.active_downloads: Dict[str, asyncio.Task] = {}
        self.max_history_size = 1000

        # Semaphore for limiting concurrent downloads
        self.download_semaphore = asyncio.Semaphore(self.concurrent_downloads)

    async def on_initialize_async(self):
        """Initialize the image download service."""
        # Load settings from settings service if available
        await self._load_settings()
        logger.info("Image download service initialized")

    async def on_start_async(self):
        """Start the image download service."""
        logger.info("Image download service started")

    async def on_shutdown_async(self):
        """Shutdown the image download service."""
        # Cancel any active downloads
        for task in self.active_downloads.values():
            if not task.done():
                task.cancel()

        # Wait for active downloads to complete
        if self.active_downloads:
            await asyncio.gather(*self.active_downloads.values(), return_exceptions=True)

        self.active_downloads.clear()
        self.download_history.clear()

        logger.info("Image download service shutdown")

    async def download_image(
        self,
        url: str,
        output_path: str,
        create_thumbnails: bool = True
    ) -> DownloadResult:
        """
        Download an image from URL.

        Args:
            url: Image URL to download
            output_path: Local path to save the image
            create_thumbnails: Whether to create thumbnails after download

        Returns:
            DownloadResult with operation details
        """
        import time

        start_time = time.time()

        # Create download result
        result = DownloadResult(
            url=url,
            local_path=output_path,
            success=False
        )

        try:
            # Acquire semaphore to limit concurrent downloads
            async with self.download_semaphore:
                # Perform the download
                await self._download_file(url, output_path)

                # Get file size
                if os.path.exists(output_path):
                    result.file_size = os.path.getsize(output_path)
                    result.success = True

                    # Create thumbnails if requested
                    if create_thumbnails:
                        await self._create_thumbnails_for_image(output_path)

                # Add to history
                result.download_time = time.time() - start_time
                await self._add_to_history(result)

                logger.debug(f"Downloaded image: {url} -> {output_path}")
                return result

        except Exception as e:
            result.error_message = str(e)
            result.download_time = time.time() - start_time

            # Add failed download to history
            await self._add_to_history(result)

            logger.error(f"Failed to download image {url}: {e}")
            return result

    async def download_images_batch(
        self,
        downloads: List[Dict[str, str]],
        create_thumbnails: bool = True
    ) -> str:
        """
        Download multiple images in batch.

        Args:
            downloads: List of dicts with 'url' and 'output_path' keys
            create_thumbnails: Whether to create thumbnails after download

        Returns:
            Operation ID for progress tracking
        """
        # Start progress tracking
        progress_service = await self._get_progress_service()
        operation_id = None

        if progress_service:
            operation_id = await progress_service.start_operation(
                "batch_download_images",
                total_steps=len(downloads),
                metadata={"total_images": len(downloads)}
            )

        # Create download tasks
        tasks = []
        for i, download_info in enumerate(downloads):
            url = download_info.get('url')
            output_path = download_info.get('output_path')

            if url and output_path:
                task = asyncio.create_task(
                    self._download_with_progress(
                        url,
                        output_path,
                        create_thumbnails,
                        operation_id,
                        progress_service,
                        i + 1,
                        len(downloads)
                    )
                )
                tasks.append(task)

        # Wait for all downloads to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Complete progress tracking
        if operation_id and progress_service:
            await progress_service.complete_operation(operation_id)

        return operation_id or "completed"

    async def _download_with_progress(
        self,
        url: str,
        output_path: str,
        create_thumbnails: bool,
        operation_id: Optional[str],
        progress_service: Optional[Any],
        current_index: int,
        total_count: int
    ) -> DownloadResult:
        """
        Download image with progress tracking.

        Args:
            url: Image URL
            output_path: Local output path
            create_thumbnails: Whether to create thumbnails
            operation_id: Progress operation ID
            progress_service: Progress service instance
            current_index: Current download index
            total_count: Total number of downloads

        Returns:
            DownloadResult
        """
        result = await self.download_image(url, output_path, create_thumbnails)

        # Update progress
        if operation_id and progress_service:
            await progress_service.update_progress(
                operation_id,
                current_index,
                metadata={
                    "current_download": current_index,
                    "total_downloads": total_count,
                    "current_url": url,
                    "success": result.success
                }
            )

        return result

    async def _download_file(self, url: str, output_path: str) -> None:
        """
        Download file from URL to local path.

        Args:
            url: File URL
            output_path: Local output path
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Download with retry logic
        for attempt in range(self.retry_attempts):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.get(url) as response:
                        response.raise_for_status()

                        # Write file in chunks
                        async with aiofiles.open(output_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(self.chunk_size):
                                await f.write(chunk)

                return  # Success

            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    raise  # Final attempt failed

                logger.warning(f"Download attempt {attempt + 1} failed for {url}: {e}")
                await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff

    async def _create_thumbnails_for_image(self, image_path: str) -> None:
        """
        Create thumbnails for a downloaded image.

        Args:
            image_path: Path to the downloaded image
        """
        try:
            # Get thumbnail cache service
            thumbnail_service = await self._get_thumbnail_service()
            if thumbnail_service:
                # Get supported sizes from settings
                supported_sizes = await self._get_thumbnail_sizes()

                # Create thumbnails for all sizes
                for size in supported_sizes:
                    try:
                        await thumbnail_service.get_thumbnail_path(image_path, size)
                    except Exception as e:
                        logger.warning(f"Failed to create thumbnail {size}px for {image_path}: {e}")

        except Exception as e:
            logger.warning(f"Could not create thumbnails for {image_path}: {e}")

    async def _get_thumbnail_sizes(self) -> List[int]:
        """Get supported thumbnail sizes from settings."""
        try:
            if self.message_bus:
                # Try to get thumbnail sizes from settings
                await self.message_bus.publish_async(
                    "settings.get",
                    key="app.download.thumbnail_sizes"
                )
                # For now, return default sizes
                return [64, 128, 256, 512]
        except:
            pass

        return [64, 128, 256, 512]

    async def _get_thumbnail_service(self) -> Optional[ThumbnailCacheService]:
        """Get thumbnail cache service instance."""
        try:
            # For now, return None - thumbnail service integration
            # will be handled by the main application through message bus events
            return None
        except:
            pass
        return None

    async def _load_settings(self):
        """Load settings from settings service."""
        try:
            if self.message_bus:
                await self.message_bus.publish_async(
                    "settings.get",
                    key="app.download"
                )
                # Settings will be applied by the main application
        except Exception as e:
            logger.warning(f"Could not load download settings: {e}")

    async def _add_to_history(self, result: DownloadResult):
        """Add download result to history."""
        self.download_history.append(result)

        # Trim history if too large
        if len(self.download_history) > self.max_history_size:
            self.download_history = self.download_history[-self.max_history_size:]

    async def _get_progress_service(self) -> Optional[Any]:
        """Get progress service instance."""
        try:
            # For now, return None - progress service integration
            # will be handled by the main application
            return None
        except:
            pass
        return None

    def get_download_history(self) -> List[DownloadResult]:
        """
        Get download history.

        Returns:
            List of recent download results
        """
        return self.download_history.copy()

    def get_download_stats(self) -> Dict[str, Any]:
        """
        Get download service statistics.

        Returns:
            Dictionary with download statistics
        """
        if not self.download_history:
            return {
                "total_downloads": 0,
                "successful_downloads": 0,
                "failed_downloads": 0,
                "total_size_mb": 0.0,
                "average_download_time": 0.0
            }

        successful = [d for d in self.download_history if d.success]
        failed = [d for d in self.download_history if not d.success]

        total_size = sum(d.file_size for d in successful)
        total_time = sum(d.download_time for d in self.download_history)

        return {
            "total_downloads": len(self.download_history),
            "successful_downloads": len(successful),
            "failed_downloads": len(failed),
            "success_rate": len(successful) / len(self.download_history) * 100,
            "total_size_mb": total_size / (1024 * 1024),
            "average_download_time": total_time / len(self.download_history),
            "concurrent_downloads": self.concurrent_downloads,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts
        }

    def clear_download_history(self):
        """Clear download history."""
        self.download_history.clear()
        logger.info("Download history cleared")

    def cancel_all_downloads(self):
        """Cancel all active downloads."""
        for task in self.active_downloads.values():
            if not task.done():
                task.cancel()

        self.active_downloads.clear()
        logger.info("Cancelled all active downloads")

    def get_active_download_count(self) -> int:
        """Get number of active downloads."""
        return len([task for task in self.active_downloads.values() if not task.done()])
