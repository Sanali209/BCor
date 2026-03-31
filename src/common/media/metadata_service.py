"""Async Media Metadata Service for BCor Common.

Provides unified access to EXIF, XMP, and IPTC via ExifTool. 

Rationale:
    Standard Python metadata libraries (pyexiv2, pillow) often have limited 
    support for video or complex XMP schemas. We wrap the industry-standard 
    `exiftool.exe` as an external binary to ensure $100\%$ metadata fidelity.
    Operations are offloaded to threads for async safety.

Environment Variables:
    - `BCOR_EXIFTOOL_PATH`: Path to a custom exiftool.exe binary.

Example:
    >>> service = MetadataService()
    >>> fs = OSFS("./images")
    >>> tags = await service.read_metadata(fs, "photo.jpg")
    >>> print(tags.get("EXIF:DateTimeOriginal"))
"""
from __future__ import annotations
import asyncio
import os
import json
import subprocess
from typing import Dict, Any, Optional, List, Union
from loguru import logger
from fs.base import FS

class MetadataService:
    """High-level service for reading and writing media metadata."""

    def __init__(self, exiftool_path: Optional[str] = None):
        # Default path to bundled exiftool if not provided
        self.exiftool_path = exiftool_path or self._find_exiftool()
        self._has_exiftool = os.path.exists(self.exiftool_path) if self.exiftool_path else False

    def _find_exiftool(self) -> Optional[str]:
        """Attempts to find the bundled or system exiftool.exe."""
        # Check environment first
        env_path = os.environ.get("BCOR_EXIFTOOL_PATH")
        if env_path and os.path.exists(env_path):
            return env_path
            
        # Check common project locations (bundled in legacy)
        bundled_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../legacy/sanali/Python/SLM/exiftool.exe"))
        if os.path.exists(bundled_path):
            return bundled_path
            
        return None

    async def read_metadata(self, fs: FS, path: str) -> Dict[str, Any]:
        """Reads all metadata for a file in the given VFS."""
        if not self._has_exiftool:
            logger.warning("ExifTool binary not found. Metadata reading disabled.")
            return {}

        # Exiftool needs a local path. If VFS is not an OSFS, we might need a temp file.
        # For now, we assume OSFS or local-adjacent paths as per monorepo usage.
        local_path = fs.getsyspath(path)
        
        return await asyncio.to_thread(self._read_sync, local_path)

    def _read_sync(self, local_path: str) -> Dict[str, Any]:
        """Synchronous read wrapper for ExifToolHelper or Subprocess."""
        try:
            import exiftool
            with exiftool.ExifToolHelper(executable=self.exiftool_path) as et:
                metadata = et.get_metadata(local_path)
                return metadata[0] if metadata else {}
        except (ImportError, Exception) as e:
            logger.debug(f"PyExifTool fallback to subprocess for {local_path}: {e}")
            return self._read_subprocess(local_path)

    def _read_subprocess(self, local_path: str) -> Dict[str, Any]:
        """Fallback reading using direct subprocess calls to exiftool.exe."""
        try:
            cmd = [self.exiftool_path, "-j", "-G", local_path]
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            return json.loads(output)[0]
        except Exception as e:
            logger.error(f"Failed to read metadata via subprocess: {e}")
            return {}

    async def write_metadata(self, fs: FS, path: str, tags: Dict[str, Any]) -> bool:
        """Writes metadata tags to a file in the given VFS."""
        if not self._has_exiftool:
            return False
            
        local_path = fs.getsyspath(path)
        return await asyncio.to_thread(self._write_sync, local_path, tags)

    def _write_sync(self, local_path: str, tags: Dict[str, Any]) -> bool:
        """Synchronous write wrapper."""
        try:
            import exiftool
            with exiftool.ExifToolHelper(executable=self.exiftool_path) as et:
                et.set_tags(local_path, tags=tags, params=["-overwrite_original"])
                return True
        except Exception as e:
            logger.error(f"Failed to write metadata for {local_path}: {e}")
            return False
