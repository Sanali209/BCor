"""TDD tests for Phase 1: AGM Stored multi-source fields extension.

Tests are written FIRST (red), then implementation follows (green).
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Annotated, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.agm.messages import StoredFieldRecalculationRequested
from src.modules.agm.metadata import Stored


# ─── Phase 1.1: Stored Metadata ──────────────────────────────────────────────

class TestStoredMetadata:
    def test_stored_accepts_single_source_field_backward_compat(self):
        """Backward compatible: original source_field still works."""
        s = Stored(source_field="uri")
        assert s.source_field == "uri"
        assert s.source_fields is None

    def test_stored_accepts_multiple_source_fields(self):
        """NEW: source_fields can be a list of trigger fields."""
        s = Stored(source_fields=["exif_data", "llm_tags"])
        assert s.source_fields == ["exif_data", "llm_tags"]
        assert s.source_field is None

    def test_stored_accepts_mime_scope(self):
        """NEW: mime_scope enables MIME-based handler dispatch."""
        s = Stored(source_field="uri", mime_scope="image/*")
        assert s.mime_scope == "image/*"

    def test_stored_accepts_context_metadata(self):
        """NEW: context_metadata allows per-field handler config."""
        s = Stored(source_field="uri", context_metadata={"chunk_size": 500})
        assert s.context_metadata["chunk_size"] == 500

    def test_stored_defaults_are_none(self):
        """All new fields default to None/empty to preserve backward compat."""
        s = Stored(source_field="uri")
        assert s.mime_scope is None
        assert s.context_metadata == {}
        assert s.source_fields is None

    def test_stored_raises_if_neither_source_given(self):
        """Must provide source_field OR source_fields, not neither."""
        with pytest.raises((ValueError, TypeError)):
            Stored()


# ─── Phase 1.2: Event Payload ────────────────────────────────────────────────

class TestStoredFieldRecalculationRequested:
    def test_event_has_original_fields(self):
        """Backward compat: original fields still present."""
        ev = StoredFieldRecalculationRequested(
            node_id="abc", field_name="summary", new_source_val="text"
        )
        assert ev.node_id == "abc"
        assert ev.field_name == "summary"
        assert ev.new_source_val == "text"

    def test_event_carries_mime_type(self):
        """NEW: mime_type propagated to enable MIME-based dispatch."""
        ev = StoredFieldRecalculationRequested(
            node_id="abc", field_name="thumbnail",
            new_source_val="file://a.jpg", mime_type="image/jpeg"
        )
        assert ev.mime_type == "image/jpeg"

    def test_event_carries_context_metadata(self):
        """NEW: context_metadata passed through to handler."""
        ev = StoredFieldRecalculationRequested(
            node_id="abc", field_name="raw_text",
            new_source_val="file://doc.pdf",
            context_metadata={"ocr_lang": "ru", "chunk_size": 300}
        )
        assert ev.context_metadata["ocr_lang"] == "ru"

    def test_event_defaults_mime_to_empty(self):
        """Backward compat: mime_type defaults to '' if not given."""
        ev = StoredFieldRecalculationRequested(
            node_id="x", field_name="y", new_source_val="z"
        )
        assert ev.mime_type == ""
        assert ev.context_metadata == {}


# ─── Phase 1.3: mapper.save() Multi-Source Dispatch ─────────────────────────

@pytest.mark.asyncio
class TestMapperMultiSourceSave:
    """Tests that mapper.save() triggers events for multi-source Stored fields."""

    def _make_mapper(self):
        from src.modules.agm.mapper import AGMMapper
        container = AsyncMock()
        bus = AsyncMock()
        return AGMMapper(container, bus), bus

    async def test_save_dispatches_when_single_source_changes(self):
        """Classic single source_field — unchanged behavior."""
        mapper, bus = self._make_mapper()

        @dataclass
        class Model:
            id: str
            uri: str
            summary: Annotated[str, Stored(source_field="uri")] = ""

        model = Model(id="1", uri="new_uri")
        prev = {"uri": "old_uri"}
        await mapper.save(model, previous_state=prev, session=None)
        bus.dispatch.assert_awaited_once()
        event = bus.dispatch.call_args[0][0]
        assert event.field_name == "summary"

    async def test_save_dispatches_when_any_multi_source_changes(self):
        """Multi-source: event fired if EITHER source_field changed."""
        mapper, bus = self._make_mapper()

        @dataclass
        class Model:
            id: str
            exif_data: dict = field(default_factory=dict)
            llm_tags: list = field(default_factory=list)
            merged_tags: Annotated[
                list,
                Stored(source_fields=["exif_data", "llm_tags"])
            ] = field(default_factory=list)

        model = Model(id="1", exif_data={"kw": ["cat"]}, llm_tags=["feline"])
        prev = {"exif_data": {}, "llm_tags": []}
        await mapper.save(model, previous_state=prev, session=None)
        assert bus.dispatch.await_count >= 1

    async def test_save_no_dispatch_when_sources_unchanged(self):
        """No event if multi-source fields did not change."""
        mapper, bus = self._make_mapper()

        @dataclass
        class Model:
            id: str
            exif_data: dict = field(default_factory=dict)
            merged_tags: Annotated[
                list,
                Stored(source_fields=["exif_data"])
            ] = field(default_factory=list)

        data = {"Keywords": ["cat"]}
        model = Model(id="1", exif_data=data)
        prev = {"exif_data": data}  # same content
        await mapper.save(model, previous_state=prev, session=None)
        bus.dispatch.assert_not_awaited()

    async def test_event_carries_mime_type_from_asset(self):
        """mime_type from model is forwarded in the event."""
        mapper, bus = self._make_mapper()

        @dataclass
        class Model:
            id: str
            mime_type: str
            uri: str
            thumbnail: Annotated[
                bytes,
                Stored(source_field="uri", mime_scope="image/*")
            ] = b""

        model = Model(id="1", mime_type="image/jpeg", uri="file://a.jpg")
        prev = {"uri": ""}
        await mapper.save(model, previous_state=prev, session=None)
        event = bus.dispatch.call_args[0][0]
        assert event.mime_type == "image/jpeg"
