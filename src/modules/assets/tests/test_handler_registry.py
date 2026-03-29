"""TDD tests for Phase 2: HandlerRegistry and ProcessingContext.

Tests are written FIRST (red), then implementation follows (green).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from src.modules.assets.domain.context import ProcessingContext
from src.modules.assets.infrastructure.registry import HandlerRegistry


# ─── Stub handlers ───────────────────────────────────────────────────────────

class GenericHandler:
    async def run(self, ctx: ProcessingContext) -> Any: ...

class ImageHandler:
    async def run(self, ctx: ProcessingContext) -> Any: ...

class PDFHandler:
    async def run(self, ctx: ProcessingContext) -> Any: ...

class SVGHandler:
    async def run(self, ctx: ProcessingContext) -> Any: ...

class VideoHandler:
    async def run(self, ctx: ProcessingContext) -> Any: ...


# ─── HandlerRegistry Tests ───────────────────────────────────────────────────

class TestHandlerRegistry:
    def test_resolves_exact_mime(self):
        reg = HandlerRegistry()
        reg.register("application/pdf", PDFHandler)
        assert reg.resolve("application/pdf") is PDFHandler

    def test_resolves_glob_category(self):
        reg = HandlerRegistry()
        reg.register("image/*", ImageHandler)
        assert reg.resolve("image/jpeg") is ImageHandler
        assert reg.resolve("image/png") is ImageHandler
        assert reg.resolve("image/webp") is ImageHandler

    def test_exact_beats_glob(self):
        """Exact MIME pattern has higher priority than glob."""
        reg = HandlerRegistry()
        reg.register("image/*", ImageHandler)
        reg.register("image/svg+xml", SVGHandler)
        assert reg.resolve("image/svg+xml") is SVGHandler
        assert reg.resolve("image/jpeg") is ImageHandler

    def test_fallback_wildcard(self):
        reg = HandlerRegistry()
        reg.register("*/*", GenericHandler)
        assert reg.resolve("application/unknown") is GenericHandler
        assert reg.resolve("x-custom/data") is GenericHandler

    def test_returns_none_when_no_match(self):
        reg = HandlerRegistry()
        assert reg.resolve("application/pdf") is None

    def test_glob_beats_wildcard(self):
        """Category glob (image/*) has higher priority than */*."""
        reg = HandlerRegistry()
        reg.register("*/*", GenericHandler)
        reg.register("image/*", ImageHandler)
        assert reg.resolve("image/jpeg") is ImageHandler

    def test_register_multiple_types(self):
        reg = HandlerRegistry()
        reg.register("image/*", ImageHandler)
        reg.register("video/*", VideoHandler)
        reg.register("application/pdf", PDFHandler)
        assert reg.resolve("image/webp") is ImageHandler
        assert reg.resolve("video/mp4") is VideoHandler
        assert reg.resolve("application/pdf") is PDFHandler

    def test_overwrite_same_pattern(self):
        """Registering the same pattern twice uses the latest."""
        reg = HandlerRegistry()
        reg.register("image/*", ImageHandler)
        reg.register("image/*", SVGHandler)
        assert reg.resolve("image/jpeg") is SVGHandler

    def test_url_scheme_pattern(self):
        """Custom scheme: 'scheme:youtube' matchers."""
        reg = HandlerRegistry()
        reg.register("video/youtube", VideoHandler)
        assert reg.resolve("video/youtube") is VideoHandler

    def test_list_registered(self):
        reg = HandlerRegistry()
        reg.register("image/*", ImageHandler)
        reg.register("application/pdf", PDFHandler)
        patterns = reg.registered_patterns()
        assert "image/*" in patterns
        assert "application/pdf" in patterns


# ─── ProcessingContext Tests ──────────────────────────────────────────────────

class TestProcessingContext:
    def test_context_carries_core_fields(self):
        ctx = ProcessingContext(
            asset_id="abc",
            mime_type="image/jpeg",
            uri="file:///a.jpg",
            field_name="thumbnail_bytes",
        )
        assert ctx.asset_id == "abc"
        assert ctx.mime_type == "image/jpeg"
        assert ctx.uri == "file:///a.jpg"
        assert ctx.field_name == "thumbnail_bytes"

    def test_context_metadata_default_empty(self):
        ctx = ProcessingContext(
            asset_id="x", mime_type="text/plain", uri="file://a.txt", field_name="raw_text"
        )
        assert ctx.metadata == {}

    def test_context_carries_metadata(self):
        ctx = ProcessingContext(
            asset_id="1", mime_type="image/jpeg", uri="file://a.jpg",
            field_name="thumbnail_bytes",
            metadata={"thumb_size": (128, 128), "ocr_lang": "en"},
        )
        assert ctx.metadata["thumb_size"] == (128, 128)
        assert ctx.metadata["ocr_lang"] == "en"

    def test_context_session_defaults_none(self):
        ctx = ProcessingContext(
            asset_id="x", mime_type="*/*", uri="x", field_name="y"
        )
        assert ctx.session is None

    def test_context_accepts_session(self):
        fake_session = object()
        ctx = ProcessingContext(
            asset_id="x", mime_type="*/*", uri="x", field_name="y",
            session=fake_session,
        )
        assert ctx.session is fake_session
