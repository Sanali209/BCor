"""ContentHashHandler — Computes SHA256 hashes for assets with optimizations."""
from __future__ import annotations

import hashlib
import pathlib
from typing import Any
from loguru import logger


class ContentHashHandler:
    """Computes a SHA256 hash for a given file or resource.
    
    Supports optimization: only hashing the first N bytes for speed on huge files.
    """

    DEFAULT_CHUNK_SIZE = 64 * 1024  # 64KB
    DEFAULT_FAST_LIMIT = 8 * 1024 * 1024  # 8MB

    @classmethod
    async def run(cls, uri: str, context: dict[str, Any] | None = None) -> str | None:
        """Compute hash for the URI.
        
        Args:
            uri: Resource URI (file:// supported).
            context: May contain 'fast_hash_limit' (int).
            
        Returns:
            Hex string of the SHA256 hash.
        """
        from src.core.storage import uri_to_path
        path = uri_to_path(uri)

        if not path.exists():
            logger.error(f"ContentHashHandler: File not found at {path}")
            return None

        limit = (context or {}).get("fast_hash_limit", cls.DEFAULT_FAST_LIMIT)
        
        hasher = hashlib.sha256()
        bytes_read = 0
        
        try:
            with path.open("rb") as f:
                while True:
                    # If we have a limit, don't read beyond it
                    to_read = cls.DEFAULT_CHUNK_SIZE
                    if limit > 0:
                        to_read = min(to_read, limit - bytes_read)
                        if to_read <= 0:
                            break
                            
                    chunk = f.read(to_read)
                    if not chunk:
                        break
                        
                    hasher.update(chunk)
                    bytes_read += len(chunk)
            
            final_hash = hasher.hexdigest()
            logger.info(f"ContentHashHandler: {path.name} ({bytes_read} bytes) -> {final_hash[:8]}...")
            return final_hash
            
        except Exception as e:
            logger.error(f"ContentHashHandler failed for {path}: {e}")
            return None
