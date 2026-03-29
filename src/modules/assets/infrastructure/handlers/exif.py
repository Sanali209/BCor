"""PiexifHandler — Declarative EXIF extraction with Unicode path support."""
from __future__ import annotations

import pathlib
from typing import Any

import piexif
from loguru import logger


class PiexifHandler:
    """Handler for extracting EXIF metadata using piexif.
    
    This handler specifically addresses the "Russian paths" (non-ASCII)
    issue on Windows by reading the file content into memory as a 
    binary stream instead of passing the path string to piexif.
    """

    @staticmethod
    async def run(uri: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Extract EXIF data from the given URI.
        
        Args:
            uri: File URI (e.g. "d:/фото/image.jpg").
            context: Optional processing context.
            
        Returns:
            A dictionary of sanitized EXIF tags.
        """
        # 1. Handle URI to Path conversion (stripping file:// if present)
        clean_path = uri.replace("file://", "")
        path = pathlib.Path(clean_path)

        if not path.exists():
            logger.warning(f"PiexifHandler: File not found at {path}")
            return {}

        try:
            # 2. Robust Read: load as bytes to circumvent piexif path encoding issues
            data = path.read_bytes()
            
            # 3. Load EXIF
            exif_dict = piexif.load(data)
            
            # 4. Sanitize: convert bytes to strings where possible for graph persistence
            return PiexifHandler._sanitize_exif(exif_dict)
            
        except Exception as e:
            logger.error(f"PiexifHandler failed for {path}: {e}")
            return {}

    @staticmethod
    def _sanitize_exif(exif_dict: dict[str, Any]) -> dict[str, Any]:
        """Convert piexif byte values to serializable types."""
        sanitized = {}
        for ifd in ("0th", "Exif", "GPS", "1st"):
            for tag, value in exif_dict.get(ifd, {}).items():
                tag_name = piexif.TAGS[ifd][tag]["name"]
                if isinstance(value, bytes):
                    try:
                        sanitized[tag_name] = value.decode("utf-8", errors="replace").strip("\x00")
                    except Exception:
                        sanitized[tag_name] = str(value)
                elif isinstance(value, tuple):
                    sanitized[tag_name] = list(value)
                else:
                    sanitized[tag_name] = value
        return sanitized
