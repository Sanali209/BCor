"""ImageDedup domain: IImageDiffer port.

Abstracts the visual difference computation between two images.
Concrete adapters (OpenCV, PIL, etc.) implement this interface.
"""
from __future__ import annotations

import abc


class IImageDiffer(abc.ABC):
    """Port: compute a visual diff between two image files."""

    @abc.abstractmethod
    def compute_difference(self, path_a: str, path_b: str) -> float:
        """Return a similarity score in [0.0, 1.0].

        0.0 = identical, 1.0 = completely different.
        """
        raise NotImplementedError


class IThumbnailCache(abc.ABC):
    """Port: retrieve a cached thumbnail PIL image for a given path."""

    @abc.abstractmethod
    def get_thumbnail(self, path: str, max_size: tuple[int, int] | None = (300, 300)) -> object:
        """Return a PIL Image object scaled to *max_size*."""
        raise NotImplementedError


class IDuplicateFinder(abc.ABC):
    """Port: build an index on a list of files and find visual duplicates."""

    @abc.abstractmethod
    def build_index(self, file_paths: list[str]) -> None:
        """Index the given image files for fast similarity search."""
        raise NotImplementedError

    @abc.abstractmethod
    def find_duplicates(
        self,
        similarity_threshold: float = 0.95,
    ) -> dict[str, list[str]]:
        """Return a dict: primary_path → [duplicate_paths]."""
        raise NotImplementedError

    @abc.abstractmethod
    def find_top_similar(self, path: str, top_k: int = 6) -> list[str]:
        """Return the *top_k* most similar images to *path*."""
        raise NotImplementedError
