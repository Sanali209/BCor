"""TDD tests for Phase 4: Domain services — TagMerger, ContentChunker, AnnotationService.

Tests are written FIRST (red), then implementation follows (green).
"""
from __future__ import annotations

import pytest

from src.modules.assets.domain.models import (
    Asset,
    BoundingBoxAnnotation,
    CaptionAnnotation,
    ImageAsset,
    SingleLabelAnnotation,
)
from src.modules.assets.domain.services import (
    AnnotationService,
    ContentChunker,
    TagMerger,
)


# ─── TagMerger ───────────────────────────────────────────────────────────────

class TestTagMerger:
    def setup_method(self):
        self.merger = TagMerger()

    def test_merges_two_sources(self):
        result = self.merger.merge(
            exif_tags=["Cat", "Animal"],
            llm_tags=["Dog", "Animal"],
        )
        assert len(result) == 3  # cat, animal, dog — no dup

    def test_deduplicates_case_insensitive(self):
        result = self.merger.merge(
            exif_tags=["CAT", "Dog"],
            llm_tags=["cat", "DOG", "Fish"],
        )
        assert len(result) == 3

    def test_normalizes_to_lowercase(self):
        result = self.merger.merge(exif_tags=["Mountain"], llm_tags=[])
        assert "mountain" in result

    def test_handles_empty_exif(self):
        result = self.merger.merge(exif_tags=[], llm_tags=["tree"])
        assert result == ["tree"]

    def test_handles_empty_llm(self):
        result = self.merger.merge(exif_tags=["sun"], llm_tags=[])
        assert result == ["sun"]

    def test_both_empty_returns_empty(self):
        result = self.merger.merge(exif_tags=[], llm_tags=[])
        assert result == []

    def test_strips_whitespace(self):
        result = self.merger.merge(exif_tags=[" Cat "], llm_tags=["cat "])
        assert len(result) == 1
        assert result[0] == "cat"

    def test_filters_empty_strings(self):
        result = self.merger.merge(exif_tags=["", "cat"], llm_tags=[""])
        assert "" not in result
        assert "cat" in result


# ─── ContentChunker ──────────────────────────────────────────────────────────

class TestContentChunker:
    def setup_method(self):
        self.chunker = ContentChunker(chunk_size=100, overlap=20)

    def test_short_text_is_single_chunk(self):
        chunks = self.chunker.chunk(asset_id="a1", text="Hello world")
        assert len(chunks) == 1
        assert chunks[0].content == "Hello world"

    def test_long_text_splits_into_chunks(self):
        text = "x " * 200  # 400 chars
        chunks = self.chunker.chunk(asset_id="a1", text=text)
        assert len(chunks) > 1

    def test_chunks_have_sequential_index(self):
        text = "word " * 100
        chunks = self.chunker.chunk(asset_id="a1", text=text)
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_chunk_asset_id_set(self):
        chunks = self.chunker.chunk(asset_id="asset-99", text="short text")
        assert all(c.asset_id == "asset-99" for c in chunks)

    def test_chunk_size_respected(self):
        text = "a" * 500
        chunks = self.chunker.chunk(asset_id="a1", text=text)
        for c in chunks:
            assert len(c.content) <= 100 + 20  # chunk_size + overlap

    def test_empty_text_returns_empty(self):
        chunks = self.chunker.chunk(asset_id="a1", text="")
        assert chunks == []

    def test_custom_chunk_size(self):
        chunker = ContentChunker(chunk_size=50, overlap=0)
        text = "a" * 200
        chunks = chunker.chunk(asset_id="a1", text=text)
        assert len(chunks) == 4


# ─── AnnotationService ────────────────────────────────────────────────────────

class TestAnnotationService:
    def setup_method(self):
        self.svc = AnnotationService()

    def test_add_single_label(self):
        asset = ImageAsset(id="x", uri="file://x.jpg", name="x", mime_type="image/jpeg")
        ann = self.svc.add_single_label(asset, label="cat", annotator="model-v1")
        assert isinstance(ann, SingleLabelAnnotation)
        assert ann.label == "cat"
        assert ann.asset_id == "x"
        assert ann in asset.annotations

    def test_add_bounding_box(self):
        asset = ImageAsset(id="y", uri="file://y.jpg", name="y", mime_type="image/jpeg")
        ann = self.svc.add_bbox(
            asset, class_label="dog", x=0.1, y=0.2, w=0.3, h=0.4, confidence=0.9
        )
        assert isinstance(ann, BoundingBoxAnnotation)
        assert ann.class_label == "dog"
        assert ann.confidence == pytest.approx(0.9)
        assert ann in asset.annotations

    def test_add_caption(self):
        asset = ImageAsset(id="z", uri="file://z.jpg", name="z", mime_type="image/jpeg")
        ann = self.svc.add_caption(asset, text="A photo", language="en")
        assert isinstance(ann, CaptionAnnotation)
        assert ann.text == "A photo"

    def test_get_annotations_by_type(self):
        asset = ImageAsset(id="q", uri="file://q.jpg", name="q", mime_type="image/jpeg")
        self.svc.add_single_label(asset, label="cat")
        self.svc.add_bbox(asset, class_label="dog", x=0, y=0, w=1, h=1)
        bboxes = self.svc.get_by_type(asset, BoundingBoxAnnotation)
        assert len(bboxes) == 1
        assert bboxes[0].class_label == "dog"

    def test_remove_annotation(self):
        asset = ImageAsset(id="r", uri="file://r.jpg", name="r", mime_type="image/jpeg")
        ann = self.svc.add_single_label(asset, label="tree")
        self.svc.remove(asset, ann)
        assert ann not in asset.annotations

    def test_confidence_default_is_1(self):
        asset = ImageAsset(id="s", uri="file://s.jpg", name="s", mime_type="image/jpeg")
        ann = self.svc.add_single_label(asset, label="sky")
        assert ann.confidence == 1.0
