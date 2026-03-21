"""ImageDedup domain: IXmpMetadata port.

Abstracts reading and writing of XMP metadata (title, tags, rating).
"""
from __future__ import annotations

import abc
from typing import Any


class IXmpMetadata(abc.ABC):
    """Port: manage XMP metadata for image files."""

    @abc.abstractmethod
    def read_metadata(self, image_path: str) -> dict[str, Any]:
        """Read metadata (title, description, subjects, rating)."""
        raise NotImplementedError

    @abc.abstractmethod
    def write_metadata(
        self, 
        image_path: str, 
        title: str | None = None,
        description: str | None = None, 
        rating: int | None = None,
        subjects: list[str] | None = None
    ) -> bool:
        """Write metadata to image file."""
        raise NotImplementedError
