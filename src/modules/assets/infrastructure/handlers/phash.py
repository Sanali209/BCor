"""PHashHandler — Perceptual hashing for images."""
from __future__ import annotations

import asyncio
import pathlib
from typing import Any

import imagehash
from PIL import Image
from loguru import logger


class PHashHandler:
    """Handler for computing perceptual hashes (pHash) using imagehash.
    
    Robustly handles Unicode paths on Windows by reading file into memory.
    """

    @staticmethod
    async def run(uri: str, context: dict[str, Any] | None = None) -> str:
        """Compute pHash for the given image URI.
        
        Args:
            uri: Image file URI.
            context: Optional processing context.
            
        Returns:
            The pHash string (hex format).
        """
        def _compute():
            clean_path = uri.replace("file://", "")
            path = pathlib.Path(clean_path)

            if not path.exists():
                logger.warning(f"PHashHandler: File not found at {path}")
                return ""

            try:
                # 1. Open image robustly from bytes
                with path.open("rb") as f:
                    with Image.open(f) as img:
                        # 2. Compute pHash
                        phash = imagehash.phash(img)
                        return str(phash)
            except Exception as e:
                logger.error(f"PHashHandler failed for {path}: {e}")
                return ""

        return await asyncio.to_thread(_compute)
