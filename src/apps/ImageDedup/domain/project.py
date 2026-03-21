"""ImageDedup domain: ImageDedupProject aggregate.

Replaces the legacy `ImageSortProject` God-Object Singleton.
Manages grouped duplicates for one "project" (a root directory).
All state mutation goes through this aggregate; it emits domain events.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field

from src.apps.ImageDedup.domain.image_group import GroupType, ImageGroup
from src.apps.ImageDedup.domain.image_item import ImageItem
from src.core.domain import Aggregate
from src.core.messages import Event

_SAVE_FILENAME = "groupList.json"

__all__ = ("ImageDedupProject", "ImageGroup", "GroupType")


@dataclass
class ImageDedupProject(Aggregate):
    """Root Aggregate for the ImageDedup bounded context.

    Manages a list of `ImageGroup` entities representing clusters of
    visually similar images found in `work_path`.

    Attributes:
        project_id: Unique project identifier.
        work_path: Root directory being scanned for duplicates.
        similarity_threshold: Minimum CNN similarity score to group images.
        groups: All duplicate groups found so far.
        hidden_pairs: Set of (primary, duplicate) paths to suppress.
        image_sets: Folder paths treated as single image-sets (no cross-group collisions).
    """

    project_id: str
    work_path: str
    similarity_threshold: float = 0.95
    groups: list[ImageGroup] = field(default_factory=list)
    hidden_pairs: list[tuple[str, str]] = field(default_factory=list)
    image_sets: list[str] = field(default_factory=list)
    events: list[Event] = field(default_factory=list, init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        super().__init__()

    def __hash__(self) -> int:
        return hash(self.project_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ImageDedupProject):
            return False
        return self.project_id == other.project_id


    def load_groups(self, data: list[ImageGroup]) -> None:
        """Replace current groups with freshly-loaded data."""
        self.groups = data

    def add_groups(self, new_groups: list[ImageGroup]) -> None:
        """Append groups and clean up."""
        self.groups.extend(new_groups)
        self._remove_collision_items()
        self.remove_groups_with_single_image()
        self._sort_by_source_folder()

    def remove_groups_with_single_image(self) -> None:
        """Drop groups that have ≤1 image (useless for dedup)."""
        self.groups = [g for g in self.groups if len(g.items) > 1]

    def remove_nonexistent_images(self) -> None:
        """Remove items whose file no longer exists on disk."""
        for group in self.groups:
            group.items = [item for item in group.items if os.path.exists(item.path)]

    # ── selection helpers ──────────────────────────────────────────────────

    def get_selected_groups(self) -> list[ImageGroup]:
        return [g for g in self.groups if g.selected]

    def get_selected_images(self) -> list[ImageItem]:
        return [img for g in self.groups for img in g.items if img.selected]

    def clear_selection(self) -> None:
        for group in self.groups:
            group.selected = False
            for item in group.items:
                item.selected = False

    # ── group re-ordering ──────────────────────────────────────────────────

    def move_group_up(self, group: ImageGroup) -> None:
        idx = self.groups.index(group)
        if idx > 0:
            self.groups.pop(idx)
            self.groups.insert(idx - 1, group)

    def move_group_down(self, group: ImageGroup) -> None:
        idx = self.groups.index(group)
        if idx < len(self.groups) - 1:
            self.groups.pop(idx)
            self.groups.insert(idx + 1, group)

    def move_group_to_top(self, group: ImageGroup) -> None:
        if group in self.groups:
            self.groups.remove(group)
            self.groups.insert(0, group)

    def move_group_to_bottom(self, group: ImageGroup) -> None:
        if group in self.groups:
            self.groups.remove(group)
            self.groups.append(group)

    def delete_selected_groups(self) -> None:
        self.groups = [g for g in self.groups if not g.selected]
        self.clear_selection()

    def merge_selected_groups(self) -> None:
        selected = self.get_selected_groups()
        if len(selected) < 2:
            return
        target = selected[0]
        for other in selected[1:]:
            target.merge(other)
            self.groups.remove(other)
        self.clear_selection()

    # ── image-level mutations ──────────────────────────────────────────────

    def get_parent_group(self, item: ImageItem) -> ImageGroup | None:
        for group in self.groups:
            if item in group.items:
                return group
        return None

    def move_selected_images_to_group(self, target: ImageGroup) -> None:
        selected = self.get_selected_images()
        for item in selected:
            parent = self.get_parent_group(item)
            if parent and parent is not target:
                parent.items.remove(item)
            target.items.append(item)
        target.deduplicate_items()
        self.clear_selection()

    def move_selected_images_to_new_group(self) -> None:
        selected = self.get_selected_images()
        if not selected:
            return
        new_group = ImageGroup(group_type=GroupType.CUSTOM_GROUP)
        for item in selected:
            parent = self.get_parent_group(item)
            if parent:
                parent.items.remove(item)
            new_group.items.append(item)
        new_group.deduplicate_items()
        self.groups.append(new_group)
        self.clear_selection()

    def remove_selected_images(self) -> None:
        selected_paths = {item.path for item in self.get_selected_images()}
        for group in self.groups:
            group.items = [item for item in group.items if item.path not in selected_paths]
        self.clear_selection()

    def make_unique(self, reference_group: ImageGroup) -> None:
        """Remove items from all OTHER groups that also appear in *reference_group*."""
        ref_paths = {item.path for item in reference_group.items}
        for group in self.groups:
            if group is not reference_group:
                group.items = [item for item in group.items if item.path not in ref_paths]

    # ── hidden pairs ───────────────────────────────────────────────────────

    def add_hidden_pair(self, primary: str, duplicate: str) -> None:
        if (primary, duplicate) not in self.hidden_pairs:
            self.hidden_pairs.append((primary, duplicate))

    def apply_hidden_pairs(self) -> None:
        """Remove hidden-pair duplicates from all groups."""
        hidden = set(self.hidden_pairs)
        for group in self.groups:
            if len(group.items) < 2:
                continue
            primary = group.items[0].path
            group.items = [
                item for item in group.items
                if (primary, item.path) not in hidden
            ]

    # ── image-set collision resolution ────────────────────────────────────

    def add_image_set(self, folder_path: str) -> None:
        if folder_path not in self.image_sets:
            self.image_sets.append(folder_path)

    def _remove_collision_items(self) -> None:
        """Remove intra-folder collisions for declared image-sets."""
        self.apply_hidden_pairs()
        for folder in self.image_sets:
            for group in self.groups:
                collisions = [
                    item for item in group.items
                    if item.path.startswith(folder)
                ]
                if len(collisions) > 1:
                    # Keep first, remove the rest
                    for item in collisions[1:]:
                        group.items.remove(item)

    def _sort_by_source_folder(self) -> None:
        self.groups.sort(key=lambda g: g.items[0].path if g.items else "")

    # ── persistence helpers ────────────────────────────────────────────────

    def get_checksum(self) -> str:
        """Stable md5 of current group state (used for dirty-check on save)."""
        raw = "".join(
            g.id + "".join(item.id for item in g.items) + "".join(p.id for p in g.propositions)
            for g in self.groups
        )
        return hashlib.md5(raw.encode()).hexdigest()

    def to_json(self) -> str:
        """Serialize groups to JSON string."""
        data = [
            {
                "id": g.id,
                "label": g.label,
                "type": g.group_type.value,
                "items": [{"path": i.path, "score": i.score, "id": i.id} for i in g.items],
                "propositions": [{"path": p.path, "score": p.score, "id": p.id} for p in g.propositions],
            }
            for g in self.groups
        ]
        return json.dumps(data, indent=2, ensure_ascii=False)

    @classmethod
    def groups_from_json(cls, raw: str) -> list[ImageGroup]:
        """Deserialize groups from a JSON string produced by `to_json()`."""
        data = json.loads(raw)
        result: list[ImageGroup] = []
        for g_data in data:
            group = ImageGroup(
                id=g_data["id"],
                label=g_data["label"],
                group_type=GroupType(g_data.get("type", GroupType.SIMILAR_ITEMS.value)),
                items=[ImageItem(path=i["path"], score=i["score"], id=i["id"]) for i in g_data["items"]],
                propositions=[ImageItem(path=p["path"], score=p["score"], id=p["id"]) for p in g_data["propositions"]],
            )
            result.append(group)
        return result
