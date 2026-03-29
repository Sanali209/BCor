"""TDD tests for Phase 5: SearchService and SemanticDuplicateFinder (unit tests only).

Integration tests requiring a running Neo4j are kept in test_integration_assets.py.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.assets.domain.factory import AssetFactory
from src.modules.assets.domain.models import (
    Asset,
    ContentChunk,
    ImageAsset,
    Tag,
)
from src.modules.assets.domain.services import ContentChunker
from src.modules.assets.infrastructure.search import SearchQuery, SearchResult, SearchService
from src.modules.assets.infrastructure.dedup import SemanticDuplicateFinder


# ─── SearchQuery ─────────────────────────────────────────────────────────────

class TestSearchQuery:
    def test_minimal_query(self):
        q = SearchQuery(text="cat")
        assert q.text == "cat"
        assert q.mime_filter is None
        assert q.tag_ids == []
        assert q.chunk_mode == "parent"

    def test_full_query(self):
        q = SearchQuery(
            text="vacation",
            mime_filter="image/*",
            tag_ids=["t1", "t2"],
            chunk_mode="chunk",
        )
        assert q.mime_filter == "image/*"
        assert "t1" in q.tag_ids
        assert q.chunk_mode == "chunk"

    def test_chunk_mode_both(self):
        q = SearchQuery(text="doc", chunk_mode="both")
        assert q.chunk_mode == "both"


# ─── SearchResult ─────────────────────────────────────────────────────────────

class TestSearchResult:
    def test_asset_result(self):
        asset = AssetFactory.create("file://a.jpg")
        r = SearchResult(item=asset, score=0.95)
        assert r.score == pytest.approx(0.95)
        assert r.chunk is None

    def test_chunk_result(self):
        asset = AssetFactory.create("file://doc.pdf")
        chunk = ContentChunk(
            id="c1", asset_id=asset.id, content="Hello", chunk_index=0
        )
        r = SearchResult(item=asset, score=0.8, chunk=chunk)
        assert r.chunk is chunk


# ─── SemanticDuplicateFinder ──────────────────────────────────────────────────

class TestSemanticDuplicateFinder:
    def test_l1_hash_match_returns_duplicate(self):
        finder = SemanticDuplicateFinder()
        a1 = AssetFactory.create("file://a.jpg")
        a1.content_hash = "abc123"
        a2 = AssetFactory.create("file://b.jpg")
        a2.content_hash = "abc123"
        candidates = [a1, a2]
        groups = finder.find_exact_duplicates(candidates)
        assert len(groups) == 1
        assert set(g.id for g in groups[0]) == {a1.id, a2.id}

    def test_no_duplicates_returns_empty(self):
        finder = SemanticDuplicateFinder()
        a1 = AssetFactory.create("file://a.jpg")
        a1.content_hash = "abc"
        a2 = AssetFactory.create("file://b.jpg")
        a2.content_hash = "xyz"
        groups = finder.find_exact_duplicates([a1, a2])
        assert groups == []

    def test_l1_ignores_assets_without_hash(self):
        finder = SemanticDuplicateFinder()
        a = AssetFactory.create("file://a.jpg")
        a.content_hash = ""  # No hash computed yet
        groups = finder.find_exact_duplicates([a])
        assert groups == []

    def test_cosine_similarity_above_threshold(self):
        finder = SemanticDuplicateFinder(similarity_threshold=0.9)
        a1 = AssetFactory.create("file://a.jpg")
        a1.embedding = [1.0, 0.0, 0.0]
        a2 = AssetFactory.create("file://b.jpg")
        a2.embedding = [0.98, 0.14, 0.0]
        pairs = finder.find_similar_pairs([a1, a2])
        assert len(pairs) == 1

    def test_cosine_similarity_below_threshold(self):
        finder = SemanticDuplicateFinder(similarity_threshold=0.99)
        a1 = AssetFactory.create("file://a.jpg")
        a1.embedding = [1.0, 0.0, 0.0]
        a2 = AssetFactory.create("file://b.jpg")
        a2.embedding = [0.0, 1.0, 0.0]  # orthogonal → 0 similarity
        pairs = finder.find_similar_pairs([a1, a2])
        assert pairs == []

    def test_empty_embeddings_skipped(self):
        finder = SemanticDuplicateFinder()
        a1 = AssetFactory.create("file://a.jpg")
        a1.embedding = []
        a2 = AssetFactory.create("file://b.jpg")
        a2.embedding = []
        pairs = finder.find_similar_pairs([a1, a2])
        assert pairs == []
