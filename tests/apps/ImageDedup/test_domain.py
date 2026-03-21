"""Unit tests for ImageDedup domain layer."""
from __future__ import annotations

import pytest

from src.apps.ImageDedup.domain.image_group import ImageGroup, GroupType
from src.apps.ImageDedup.domain.image_item import ImageItem
from src.apps.ImageDedup.domain.project import ImageDedupProject


# ─── Fixtures ─────────────────────────────────────────────────────────────────


def make_item(path: str, score: float = 0.0) -> ImageItem:
    return ImageItem(path=path, score=score)


def make_group(*paths: str) -> ImageGroup:
    group = ImageGroup()
    for p in paths:
        group.items.append(make_item(p))
    return group


def make_project(*group_tuples: tuple[str, ...]) -> ImageDedupProject:
    project = ImageDedupProject(project_id="test-project", work_path="/fake")
    for paths in group_tuples:
        project.groups.append(make_group(*paths))
    return project


# ─── ImageItem tests ──────────────────────────────────────────────────────────


class TestImageItem:
    def test_equality_by_path(self) -> None:
        a = ImageItem(path="/a/b.jpg")
        b = ImageItem(path="/a/b.jpg")
        assert a == b

    def test_different_paths_not_equal(self) -> None:
        a = ImageItem(path="/a/b.jpg")
        b = ImageItem(path="/a/c.jpg")
        assert a != b

    def test_hash_by_path(self) -> None:
        a = ImageItem(path="/a/b.jpg")
        b = ImageItem(path="/a/b.jpg")
        assert hash(a) == hash(b)

    def test_unique_id_per_instance(self) -> None:
        a = ImageItem(path="/x.jpg")
        b = ImageItem(path="/y.jpg")
        assert a.id != b.id


# ─── ImageGroup tests ─────────────────────────────────────────────────────────


class TestImageGroup:
    def test_deduplication_keeps_first(self) -> None:
        group = make_group("/a.jpg", "/b.jpg", "/a.jpg")
        group.deduplicate_items()
        assert len(group.items) == 2
        assert group.items[0].path == "/a.jpg"

    def test_merge_combines_items(self) -> None:
        g1 = make_group("/a.jpg", "/b.jpg")
        g2 = make_group("/c.jpg", "/b.jpg")  # /b.jpg is dup
        g1.merge(g2)
        paths = {i.path for i in g1.items}
        assert paths == {"/a.jpg", "/b.jpg", "/c.jpg"}

    def test_get_selected_items_empty_by_default(self) -> None:
        group = make_group("/a.jpg", "/b.jpg")
        assert group.get_selected_items() == []

    def test_accept_proposition_moves_item(self) -> None:
        item = make_item("/prop.jpg")
        group = ImageGroup()
        group.propositions.append(item)
        group.accept_proposition(item)
        assert item in group.items
        assert item not in group.propositions


# ─── ImageDedupProject tests ──────────────────────────────────────────────────


class TestImageDedupProject:
    def test_remove_groups_with_single_image(self) -> None:
        project = make_project(("/a.jpg",), ("/b.jpg", "/c.jpg"))
        project.remove_groups_with_single_image()
        assert len(project.groups) == 1
        assert project.groups[0].items[0].path == "/b.jpg"

    def test_clear_selection(self) -> None:
        project = make_project(("/a.jpg", "/b.jpg"))
        project.groups[0].selected = True
        project.groups[0].items[0].selected = True
        project.clear_selection()
        assert not project.groups[0].selected
        assert not any(i.selected for i in project.groups[0].items)

    def test_delete_selected_groups(self) -> None:
        project = make_project(("/a.jpg", "/b.jpg"), ("/c.jpg", "/d.jpg"))
        project.groups[0].selected = True
        project.delete_selected_groups()
        assert len(project.groups) == 1
        assert project.groups[0].items[0].path == "/c.jpg"

    def test_merge_selected_groups(self) -> None:
        project = make_project(("/a.jpg", "/b.jpg"), ("/c.jpg", "/d.jpg"))
        project.groups[0].selected = True
        project.groups[1].selected = True
        project.merge_selected_groups()
        assert len(project.groups) == 1
        assert len(project.groups[0].items) == 4

    def test_make_unique_removes_from_others(self) -> None:
        project = make_project(("/a.jpg", "/b.jpg"), ("/b.jpg", "/c.jpg"))
        project.make_unique(project.groups[0])
        # /b.jpg should be gone from group[1]
        paths_in_g1 = {i.path for i in project.groups[1].items}
        assert "/b.jpg" not in paths_in_g1

    def test_apply_hidden_pairs(self) -> None:
        project = make_project(("/a.jpg", "/b.jpg", "/c.jpg"))
        project.add_hidden_pair("/a.jpg", "/b.jpg")
        project.apply_hidden_pairs()
        paths = [i.path for i in project.groups[0].items]
        assert "/b.jpg" not in paths
        assert "/a.jpg" in paths
        assert "/c.jpg" in paths

    def test_json_roundtrip(self) -> None:
        project = make_project(("/a.jpg", "/b.jpg"))
        raw = project.to_json()
        groups = ImageDedupProject.groups_from_json(raw)
        assert len(groups) == 1
        assert groups[0].items[0].path == "/a.jpg"

    def test_get_checksum_changes_on_mutation(self) -> None:
        project = make_project(("/a.jpg", "/b.jpg"))
        checksum_before = project.get_checksum()
        project.groups[0].items.append(make_item("/c.jpg"))
        assert project.get_checksum() != checksum_before

    def test_move_group_up(self) -> None:
        project = make_project(("/a.jpg", "/b.jpg"), ("/c.jpg", "/d.jpg"))
        g = project.groups[1]
        project.move_group_up(g)
        assert project.groups[0] is g

    def test_move_group_down(self) -> None:
        project = make_project(("/a.jpg", "/b.jpg"), ("/c.jpg", "/d.jpg"))
        g = project.groups[0]
        project.move_group_down(g)
        assert project.groups[1] is g
