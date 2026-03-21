"""ImageDedup domain entities.

ImageItem is a Value Object representing a single image path with an optional
similarity score and UI selection state.
"""
from __future__ import annotations

import uuid

__all__ = ("ImageItem",)
from dataclasses import dataclass, field


@dataclass
class ImageItem:
    """Value Object – one image in the dedup workflow.

    Attributes:
        path: Absolute filesystem path to the image file.
        score: Similarity score from 0.0 (identical) to 1.0 (different).
        selected: UI selection flag; used for batch operations.
        id: Stable unique identifier (auto-assigned).
    """

    path: str
    score: float = 0.0
    selected: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __hash__(self) -> int:
        return hash(self.path)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ImageItem):
            return self.path == other.path
        return NotImplemented
