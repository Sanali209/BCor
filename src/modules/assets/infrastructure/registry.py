"""HandlerRegistry — MIME-based dispatcher for asset processing handlers."""
from __future__ import annotations

from typing import Any


class HandlerRegistry:
    """Registry of asset processing handlers, dispatched by MIME type.

    Supports three levels of MIME matching (highest priority first):
    1. Exact match:    ``image/svg+xml``
    2. Category glob: ``image/*``
    3. Wildcard:       ``*/*``

    Example::

        registry = HandlerRegistry()
        registry.register("application/pdf", PDFHandler)
        registry.register("image/*", ImageHandler)
        registry.register("*/*", GenericHandler)

        handler_cls = registry.resolve("image/jpeg")  # → ImageHandler
    """

    def __init__(self) -> None:
        # Stores pattern → handler_class
        self._handlers: dict[str, type] = {}
        # Stores name → handler_class
        self._named_handlers: dict[str, type] = {}

    def register(self, mime_pattern: str, handler: type) -> None:
        """Register a handler for a MIME pattern."""
        self._handlers[mime_pattern] = handler

    def register_named(self, name: str, handler: type) -> None:
        """Register a handler by an explicit name."""
        self._named_handlers[name] = handler

    def resolve(self, mime_type: str, handler_name: str | None = None) -> type | None:
        """Return the best-matching handler class.

        Priority: 
        1. Explicit handler_name match.
        2. MIME exact match.
        3. MIME category glob (image/*).
        4. MIME wildcard (*/*).

        Args:
            mime_type: Full MIME type string.
            handler_name: Optional explicit handler name from metadata.
        """
        # 1. Named match
        if handler_name and handler_name in self._named_handlers:
            return self._named_handlers[handler_name]

        # 2. Exact MIME match
        if mime_type in self._handlers:
            return self._handlers[mime_type]

        # 3. Category glob (e.g. "image/*")
        category = mime_type.split("/")[0] + "/*"
        if category in self._handlers:
            return self._handlers[category]

        # 4. Wildcard fallback
        return self._handlers.get("*/*")

    def registered_patterns(self) -> list[str]:
        """Return all registered MIME patterns."""
        return list(self._handlers.keys())

    def registered_names(self) -> list[str]:
        """Return all registered named handlers."""
        return list(self._named_handlers.keys())
