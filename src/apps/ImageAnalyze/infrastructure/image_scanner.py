from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image

from ..domain.models import ImageAnalysisRecord


def scan_file(file_path: str) -> ImageAnalysisRecord | None:
    """CPU-bound task for scanning a single image file."""
    try:
        path = Path(file_path)
        with Image.open(path) as img:
            stats = path.stat()
            return ImageAnalysisRecord(
                path=str(path.absolute()),
                filename=path.name,
                extension=path.suffix.lower(),
                size_bytes=stats.st_size,
                width=img.width,
                height=img.height,
                created_at=stats.st_ctime,
                modified_at=stats.st_mtime
            )
    except Exception:
        return None

class ImageScanner:
    def __init__(self, supported_extensions: list[str] | None = None) -> None:
        self.supported_extensions = supported_extensions or [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"]

    async def scan_directory(
        self, 
        directory_path: str, 
        progress_callback: Callable[[int, int, str], Awaitable[None]] | None = None
    ) -> list[ImageAnalysisRecord]:
        directory = Path(directory_path)
        if not directory.exists():
            return []

        # Phase 1: Traverse
        if progress_callback:
            await progress_callback(0, 0, "Traversing directory structure...")
        
        files_to_process = []
        for root, _, files in os.walk(directory):
            for file in files:
                if Path(file).suffix.lower() in self.supported_extensions:
                    files_to_process.append(os.path.join(root, file))

        total = len(files_to_process)
        if total == 0:
            return []

        if progress_callback:
            await progress_callback(0, total, f"Found {total} files. Starting scan...")

        # Phase 2: Multiprocess scan
        loop = asyncio.get_event_loop()
        results = []
        processed = 0
        
        with ProcessPoolExecutor() as executor:
            # We use small chunks to keep the event loop responsive
            chunk_size = 500
            for i in range(0, total, chunk_size):
                chunk = files_to_process[i : i + chunk_size]
                futures = [loop.run_in_executor(executor, scan_file, f) for f in chunk]
                
                chunk_results = await asyncio.gather(*futures)
                for res in chunk_results:
                    if res:
                        results.append(res)
                
                processed += len(chunk)
                if progress_callback:
                    await progress_callback(processed, total, f"Scanned {processed}/{total} images...")

        if progress_callback:
            await progress_callback(total, total, "Scan complete!")
            
        return results
