"""
Path utility functions for the DuckDuckGo Image Search application.
"""

import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple


def ensure_directory(path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to create

    Returns:
        True if directory exists or was created successfully
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def get_cache_path(subfolder: str = "") -> str:
    """
    Get the cache directory path.

    Args:
        subfolder: Optional subfolder within cache

    Returns:
        Full path to cache directory
    """
    base_cache = Path("cache")
    if subfolder:
        return str(base_cache / subfolder)
    return str(base_cache)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem
    """
    import re
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    sanitized = re.sub(r'\s+', '_', sanitized)
    # Limit length
    if len(sanitized) > 100:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:96] + ext
    return sanitized


def get_file_hash(file_path: str, algorithm: str = "md5") -> Optional[str]:
    """
    Calculate hash of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use

    Returns:
        Hex string of file hash or None if error
    """
    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception:
        return None


def get_thumbnail_path(full_path: str, size: int, cache_dir: Optional[str] = None) -> str:
    """
    Generate thumbnail path for a full image path.

    Args:
        full_path: Path to the full-size image
        size: Thumbnail size in pixels
        cache_dir: Cache directory (uses default if None)

    Returns:
        Full path where thumbnail should be stored
    """
    if cache_dir is None:
        cache_dir = get_cache_path("thumbnails")

    # Create hash of original path for unique filename
    path_hash = hashlib.md5(full_path.encode()).hexdigest()[:16]

    # Ensure cache directory exists
    size_dir = os.path.join(cache_dir, f"{size}x{size}")
    ensure_directory(size_dir)

    # Return thumbnail path
    filename = f"{path_hash}.jpg"
    return os.path.join(size_dir, filename)


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in MB
    """
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except OSError:
        return 0.0


def is_image_file(file_path: str) -> bool:
    """
    Check if file is an image based on extension.

    Args:
        file_path: Path to check

    Returns:
        True if file has image extension
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'}
    return Path(file_path).suffix.lower() in image_extensions


def get_safe_filename(url: str, default: str = "image") -> str:
    """
    Generate a safe filename from a URL or use default.

    Args:
        url: Source URL
        default: Default filename if URL parsing fails

    Returns:
        Safe filename
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if filename and '.' in filename:
            return sanitize_filename(filename)
    except Exception:
        pass

    return f"{sanitize_filename(default)}.jpg"


def cleanup_path(path: str) -> str:
    """
    Clean up a file path by resolving relative components.

    Args:
        path: Path to clean

    Returns:
        Cleaned absolute path
    """
    return os.path.abspath(os.path.expanduser(path))


def get_relative_path(full_path: str, base_path: str) -> str:
    """
    Get relative path from base path.

    Args:
        full_path: Full path to convert
        base_path: Base path for relative calculation

    Returns:
        Relative path or original path if not relative
    """
    try:
        return os.path.relpath(full_path, base_path)
    except ValueError:
        return full_path
