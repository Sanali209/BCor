"""ImageDedup domain: ImageGroup entity.

An ImageGroup is a set of images that are suspected duplicates of each other.
The first item in `items` is conventionally the "primary" image.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum

from src.apps.ImageDedup.domain.image_item import ImageItem

__all__ = ("ImageGroup", "GroupType")


class GroupType(Enum):
    """Classification of how the group was created."""

    FOLDER_ITEMS = "folder_items"
    SIMILAR_ITEMS = "similar_items"
    CUSTOM_GROUP = "custom_group"


@dataclass
class ImageGroup:
    """Entity: a cluster of images treated as potential duplicates.

    Attributes:
        id: Stable unique identifier.
        label: Human-readable group name (usually the primary filename).
        group_type: How the group was assembled.
        selected: Whether the whole group is selected in the UI.
        expanded: Whether the group widget is expanded in the UI.
        items: The actual images in this group.
        propositions: Similar images *suggested* but not yet confirmed.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    label: str = field(default="")
    group_type: GroupType = GroupType.SIMILAR_ITEMS
    selected: bool = False
    expanded: bool = True
    items: list[ImageItem] = field(default_factory=list)
    propositions: list[ImageItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.id

    # ── item path helpers ──────────────────────────────────────────────────

    def item_paths(self) -> list[str]:
        """Return flat list of paths for all items in this group."""
        return [item.path for item in self.items]

    def get_selected_items(self) -> list[ImageItem]:
        """Return items that have the selection flag set."""
        return [item for item in self.items if item.selected]

    # ── mutation helpers ───────────────────────────────────────────────────

    def deduplicate_items(self) -> None:
        """Remove duplicate paths, keeping first occurrence."""
        seen: dict[str, ImageItem] = {}
        for item in self.items:
            seen.setdefault(item.path, item)
        self.items = list(seen.values())

    def merge(self, other: ImageGroup) -> None:
        """Absorb all items and propositions from *other* into this group."""
        self.items.extend(other.items)
        self.propositions.extend(other.propositions)
        self.deduplicate_items()

    def accept_proposition(self, item: ImageItem) -> None:
        """Move *item* from propositions → confirmed items."""
        if item in self.propositions:
            self.propositions.remove(item)
        self.items.append(item)
        self.deduplicate_items()
