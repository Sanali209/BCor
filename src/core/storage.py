"""CAS Storage Utilities for BCor.

Provides content-addressable storage logic with sharding to ensure
high performance on Windows/ext4 filesystems with millions of files.
"""
from __future__ import annotations

import pathlib
from typing import Literal

# Default sizes for the 10x pipeline
ThumbnailSize = Literal["small", "medium", "large", "original"]
SIZE_MAP: dict[ThumbnailSize, tuple[int, int]] = {
    "small": (128, 128),
    "medium": (512, 512),
    "large": (1024, 1024),
}

def get_cas_path(root: str | pathlib.Path, content_hash: str, size: ThumbnailSize = "medium") -> pathlib.Path:
    """Calculate the sharded path for a given content hash and size.
    
    Structure: ROOT / thumbs / ab / cd / {hash}_{size}.png
    
    Args:
        root: Storage root directory (e.g., 'data').
        content_hash: SHA256 or MD5 hash of the content.
        size: Target size name.
        
    Returns:
        A pathlib.Path object pointing to the expected file location.
    """
    if not content_hash or len(content_hash) < 4:
        raise ValueError(f"Invalid content hash: {content_hash}")

    # Use first 4 chars for 2-level nesting (256 * 256 = 65,536 shards)
    shard1 = content_hash[0:2].lower()
    shard2 = content_hash[2:4].lower()
    
    filename = f"{content_hash}_{size}.png"
    
    return pathlib.Path(root) / "thumbs" / shard1 / shard2 / filename

def ensure_cas_dir(path: pathlib.Path) -> None:
    """Ensure the directory for the given CAS path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)

def uri_to_path(uri: str | pathlib.Path) -> pathlib.Path:
    """Robustly convert a file:// URI to a local pathlib.Path.
    
    Handles Windows path nuances (e.g. file:///C:/... -> C:/...)
    and platform-independent slashes.
    """
    if isinstance(uri, pathlib.Path):
        return uri
        
    if not uri.startswith("file://"):
        return pathlib.Path(uri)
        
    # Standard: file:///D:/path -> /D:/path -> D:/path
    clean_path = uri.replace("file://", "")
    
    # Handle Windows: /D:/path -> D:/path
    if len(clean_path) > 2 and clean_path[0] == "/" and clean_path[2] == ":":
        clean_path = clean_path[1:]
        
    return pathlib.Path(clean_path)

