"""EasyOCR — OCR handler for ImageAsset (Stub)."""
from __future__ import annotations

from typing import Any
from loguru import logger

class EasyOCRHandler:
    """Stub for EasyOCR implementation."""

    @staticmethod
    async def run(uri: str, context: dict[str, Any] | None = None) -> str:
        """Stub for OCR run.
        
        Args:
            uri: Image URI.
            context: Optional context.

        Returns:
            Empty string for now.
        """
        logger.warning(f"EasyOCRHandler: Stub called for {uri}. Full implementation requires 'easyocr' package.")
        return ""
