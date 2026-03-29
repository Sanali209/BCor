"""Pyexiv2Handler — Professional metadata management with XMP read/write support."""
from __future__ import annotations

import pathlib
from typing import Any
import pyexiv2
from loguru import logger


class Pyexiv2Handler:
    """Universal handler for image metadata using pyexiv2.
    
    Supports reading and writing EXIF, IPTC, and XMP metadata.
    Specifically optimized for WebP and modern image formats on Windows.
    """

    @staticmethod
    async def run(uri: str, context: dict[str, Any] | None = None) -> Any:
        """Extract or write metadata depending on context.
        
        Args:
            uri: File URI.
            context: Processing context containing 'field_name' and 'new_source_val'.
            
        Returns:
            Metadata dict for read mode, or bool for write mode.
        """
        field_name = context.get("field_name") if context else None
        
        # --- WRITE MODE: xmp_sync ---
        if field_name == "xmp_sync":
            tags_to_write = {}
            new_val = context.get("new_source_val", [])
            
            if isinstance(new_val, list) and new_val:
                # Map auto_tags to standard Dubin Core subject
                tags_to_write["Xmp.dc.subject"] = ", ".join(str(v) for v in new_val)
            elif isinstance(new_val, str) and new_val:
                tags_to_write["Xmp.dc.subject"] = new_val
            
            if tags_to_write:
                return await Pyexiv2Handler.write_xmp(uri, tags_to_write)
            return True

        # --- READ MODE: exif_data or xmp_data ---
        clean_path = uri.replace("file://", "")
        # Resolve to absolute path for pyexiv2
        path = str(pathlib.Path(clean_path).absolute())

        if not pathlib.Path(path).exists():
            logger.warning(f"Pyexiv2Handler: File not found at {path}")
            return {}

        results = {
            "exif": {},
            "iptc": {},
            "xmp": {}
        }

        img = None
        try:
            # Use pyexiv2.Image which handles Windows paths well
            img = pyexiv2.Image(path)
            
            # If specifically requested xmp_data, return just xmp for cleaner graph
            if field_name == "xmp_data":
                return Pyexiv2Handler._sanitize(img.read_xmp())
            if field_name == "exif_data":
                return Pyexiv2Handler._sanitize(img.read_exif())

            # Fallback for generic calls or debug
            results["exif"] = Pyexiv2Handler._sanitize(img.read_exif())
            results["iptc"] = Pyexiv2Handler._sanitize(img.read_iptc())
            results["xmp"] = Pyexiv2Handler._sanitize(img.read_xmp())
            
            return results
        except Exception as e:
            logger.error(f"Pyexiv2Handler read failed for {path}: {e}")
            return {}
        finally:
            if img:
                img.close()

    @staticmethod
    def _sanitize(data: dict[str, Any]) -> dict[str, Any]:
        """Convert pyexiv2 values to graph-serializable types."""
        sanitized = {}
        for k, v in data.items():
            if isinstance(v, list):
                # Standardize lists to strings if they are simple tag lists
                if all(isinstance(i, str) for i in v):
                    sanitized[k] = ", ".join(v)
                else:
                    sanitized[k] = v
            else:
                sanitized[k] = v
        return sanitized

    @staticmethod
    async def write_xmp(uri: str, tags: dict[str, str]) -> bool:
        """Write XMP metadata tags back to the image file.
        
        Args:
            uri: File URI.
            tags: Dictionary of XMP tags to modify (e.g., {"Xmp.dc.subject": "tag1, tag2"}).
            
        Returns:
            True if successful.
        """
        clean_path = uri.replace("file://", "")
        path = str(pathlib.Path(clean_path).absolute())

        img = None
        try:
            img = pyexiv2.Image(path)
            img.modify_xmp(tags)
            logger.info(f"Successfully wrote XMP tags to {path}")
            return True
        except Exception as e:
            logger.error(f"Pyexiv2Handler write fail for {path}: {e}")
            return False
        finally:
            if img:
                img.close()
