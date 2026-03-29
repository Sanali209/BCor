"""TDD tests for Phase 3: Domain Models, AssetFactory, Annotations and Albums.

Tests are written FIRST (red), then implementation follows (green).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Annotated, Any, get_args, get_origin, get_type_hints

import pytest

from src.modules.assets.domain.factory import AssetFactory
from src.modules.assets.domain.models import (
    Album,
    Asset,
    BoundingBoxAnnotation,
    CaptionAnnotation,
    ContentChunk,
    DocumentAsset,
    ImageAsset,
    MultiLabelAnnotation,
    PhysicalAsset,
    PolygonAnnotation,
    SingleLabelAnnotation,
    SmartAlbum,
    Tag,
    VideoAsset,
)
from src.modules.agm.metadata import Rel, Stored


# ─── AssetFactory ─────────────────────────────────────────────────────────────

class TestAssetFactory:
    def test_youtube_url_creates_video_asset(self):
        asset = AssetFactory.create("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert isinstance(asset, VideoAsset)

    def test_youtu_be_short_url(self):
        asset = AssetFactory.create("https://youtu.be/dQw4w9WgXcQ")
        assert isinstance(asset, VideoAsset)

    def test_pdf_by_mime(self):
        asset = AssetFactory.create("file:///doc.pdf", mime="application/pdf")
        assert isinstance(asset, DocumentAsset)

    def test_pdf_by_extension(self):
        asset = AssetFactory.create("file:///report.pdf")
        assert isinstance(asset, DocumentAsset)

    def test_jpeg_creates_image_asset(self):
        asset = AssetFactory.create("file:///photo.jpg")
        assert isinstance(asset, ImageAsset)

    def test_png_creates_image_asset(self):
        asset = AssetFactory.create("file:///diagram.png")
        assert isinstance(asset, ImageAsset)

    def test_mp4_creates_video_asset(self):
        asset = AssetFactory.create("file:///movie.mp4")
        assert isinstance(asset, VideoAsset)

    def test_docx_creates_document_asset(self):
        asset = AssetFactory.create("file:///doc.docx")
        assert isinstance(asset, DocumentAsset)

    def test_unknown_extension_creates_base_asset(self):
        asset = AssetFactory.create("file:///data.bin")
        assert type(asset) is Asset

    def test_asset_has_uri_set(self):
        uri = "file:///photo.jpg"
        asset = AssetFactory.create(uri)
        assert asset.uri == uri

    def test_asset_has_mime_type_set_from_extension(self):
        asset = AssetFactory.create("file:///photo.jpg")
        assert asset.mime_type == "image/jpeg"


# ─── Base Asset Model ─────────────────────────────────────────────────────────

class TestBaseAssetModel:
    def test_asset_has_required_fields(self):
        a = Asset(id="1", uri="file:///x.pdf", name="x.pdf", mime_type="application/pdf")
        assert a.uri == "file:///x.pdf"
        assert a.mime_type == "application/pdf"

    def test_asset_content_hash_defaults_empty(self):
        a = Asset(id="1", uri="x", name="x", mime_type="*/*")
        assert a.content_hash == ""

    def test_asset_thumbnail_bytes_defaults_empty(self):
        a = Asset(id="1", uri="x", name="x", mime_type="*/*")
        assert a.thumbnail_bytes == b""

    def test_asset_tags_field_is_rel(self):
        hints = get_type_hints(Asset, include_extras=True)
        tag_type = hints.get("tags")
        assert tag_type is not None
        metas = [m for m in get_args(tag_type)[1:] if isinstance(m, Rel)]
        assert any(m.type == "HAS_TAG" for m in metas)


# ─── Annotation Tests ─────────────────────────────────────────────────────────

class TestAnnotationModels:
    def test_single_label_annotation(self):
        ann = SingleLabelAnnotation(id="a1", asset_id="x", label="cat")
        assert ann.label == "cat"

    def test_multi_label_annotation(self):
        ann = MultiLabelAnnotation(id="a2", asset_id="x", labels=["cat", "animal"])
        assert "cat" in ann.labels

    def test_caption_annotation(self):
        ann = CaptionAnnotation(id="a3", asset_id="x", text="A cat on a couch")
        assert ann.text == "A cat on a couch"
        assert ann.language == "en"

    def test_bounding_box_annotation_fields(self):
        ann = BoundingBoxAnnotation(
            id="a4", asset_id="x",
            x=0.1, y=0.2, w=0.3, h=0.4, class_label="dog"
        )
        assert ann.class_label == "dog"
        assert ann.x == pytest.approx(0.1)
        assert ann.confidence == 1.0  # default

    def test_polygon_annotation(self):
        pts = [[0.0, 0.0], [1.0, 0.0], [0.5, 1.0]]
        ann = PolygonAnnotation(id="a5", asset_id="x", points=pts, class_label="tree")
        assert len(ann.points) == 3

    def test_annotation_confidence_custom(self):
        ann = SingleLabelAnnotation(id="a6", asset_id="x", label="sky", confidence=0.85)
        assert ann.confidence == pytest.approx(0.85)


# ─── Tag Hierarchy ────────────────────────────────────────────────────────────

class TestTagHierarchy:
    def test_tag_has_name(self):
        t = Tag(id="t1", name="Animals")
        assert t.name == "Animals"

    def test_tag_parent_defaults_none(self):
        t = Tag(id="t1", name="Root")
        assert t.parent is None

    def test_tag_parent_rel_annotation(self):
        hints = get_type_hints(Tag, include_extras=True)
        parent_t = hints.get("parent")
        assert parent_t is not None
        metas = [m for m in get_args(parent_t)[1:] if isinstance(m, Rel)]
        assert any(m.type == "PARENT_TAG" for m in metas)


# ─── Albums ───────────────────────────────────────────────────────────────────

class TestAlbumModels:
    def test_album_has_name(self):
        album = Album(id="alb1", name="Holidays")
        assert album.name == "Holidays"

    def test_album_parent_defaults_none(self):
        album = Album(id="alb1", name="Root")
        assert album.parent is None

    def test_album_child_of_rel(self):
        hints = get_type_hints(Album, include_extras=True)
        parent_t = hints.get("parent")
        metas = [m for m in get_args(parent_t)[1:] if isinstance(m, Rel)]
        assert any(m.type == "CHILD_OF" for m in metas)

    def test_smart_album_stores_criteria_as_json(self):
        criteria = {"mime": "image/*", "tags": ["cat"]}
        album = SmartAlbum(id="s1", name="Cats", filter_criteria=json.dumps(criteria))
        parsed = json.loads(album.filter_criteria)
        assert parsed["tags"] == ["cat"]

    def test_smart_album_criteria_default_empty(self):
        album = SmartAlbum(id="s1", name="Empty")
        assert album.filter_criteria == "{}"


# ─── ContentChunk ─────────────────────────────────────────────────────────────

class TestContentChunk:
    def test_chunk_has_content(self):
        chunk = ContentChunk(id="c1", asset_id="a1", content="Hello world")
        assert chunk.content == "Hello world"

    def test_chunk_has_index(self):
        chunk = ContentChunk(id="c1", asset_id="a1", content="x", chunk_index=3)
        assert chunk.chunk_index == 3
