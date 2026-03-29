"""AssetFactory — dynamic asset type selection by URI/MIME/extension."""
from __future__ import annotations

import mimetypes
import uuid

from src.modules.assets.domain.models import (
    Asset,
    TextAsset,
    ImageAsset,
    VideoAsset,
)

# Extend mimetypes with common missing entries
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("video/x-matroska", ".mkv")

_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"}

_EXT_TO_MIME: dict[str, str] = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
    ".bmp": "image/bmp", ".tiff": "image/tiff",

    ".mp4": "video/mp4", ".mkv": "video/x-matroska", ".avi": "video/x-msvideo",
    ".mov": "video/quicktime", ".webm": "video/webm", ".flv": "video/x-flv",

    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword", ".odt": "application/vnd.oasis.opendocument.text",
    ".txt": "text/plain", ".md": "text/markdown", ".html": "text/html",
    ".htm": "text/html", ".csv": "text/csv",
}


class AssetFactory:
    """Creates the appropriate Asset subclass based on URI, MIME, or extension."""

    @staticmethod
    def create_from_path(path: str) -> Asset:
        """Convenience method to create an asset from a local filesystem path."""
        return AssetFactory.create(uri=f"file://{path}")

    @staticmethod
    def create(uri: str, mime: str | None = None, name: str | None = None) -> Asset:
        """Create and return the most specific Asset subclass.

        Resolution order:
        1. URL host check (YouTube → VideoAsset)
        2. Caller-provided mime override
        3. File extension guess

        Args:
            uri:  The asset URI (file://, https://, etc.)
            mime: Optional explicit MIME type override.
            name: Optional display name. Defaults to last URI segment.

        Returns:
            An instance of the appropriate Asset subclass.
        """
        resolved_mime = AssetFactory._resolve_mime(uri, mime)
        display_name = name or uri.rstrip("/").split("/")[-1] or uri
        # Resolve size and hash if local file
        size = 0
        content_hash = ""
        if uri.startswith("file://"):
            try:
                import os
                import hashlib
                path = str(uri).replace("file://", "")
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    # Simple SHA256 for CAS key
                    hasher = hashlib.sha256()
                    with open(path, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hasher.update(chunk)
                    content_hash = hasher.hexdigest()
                    from loguru import logger
                    logger.debug(f"AssetFactory: Computed hash {content_hash} for {path}")
                else:
                    from loguru import logger
                    logger.warning(f"AssetFactory: Path not found {path}")
            except Exception as e:
                from loguru import logger
                logger.error(f"AssetFactory: Hash failure for {uri}: {e}")

        asset_id = str(uuid.uuid5(uuid.NAMESPACE_URL, uri))
        kwargs = dict(
            id=asset_id, 
            uri=uri, 
            name=display_name, 
            mime_type=resolved_mime,
            description="",
            content_hash=content_hash,
            size=size
        )

        # Delegate to subclass based on resolved MIME
        if resolved_mime.startswith("image/"):
            try:
                from PIL import Image
                path = uri.replace("file://", "")
                with Image.open(path) as img:
                    kwargs["width"], kwargs["height"] = img.size
            except Exception as e:
                logger.warning(f"AssetFactory: Could not read image dimensions for {uri}: {e}")
            return ImageAsset(**kwargs)
        if resolved_mime.startswith("video/"):
            return VideoAsset(**kwargs)
        if resolved_mime in {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.oasis.opendocument.text",
            "text/plain", "text/markdown", "text/html", "text/csv",
        } or resolved_mime.startswith("text/"):
            return TextAsset(**kwargs)

        return Asset(**kwargs)

    @staticmethod
    def _resolve_mime(uri: str, override: str | None) -> str:
        if override:
            return override

        # YouTube URL check
        try:
            from urllib.parse import urlparse
            host = urlparse(uri).hostname or ""
            if host in _YOUTUBE_HOSTS:
                return "video/youtube"
        except Exception:
            pass

        # Extension-based lookup (custom map first, then stdlib)
        lower = uri.lower()
        for ext, mime in _EXT_TO_MIME.items():
            if lower.endswith(ext):
                return mime

        guessed, _ = mimetypes.guess_type(uri)
        return guessed or "application/octet-stream"
