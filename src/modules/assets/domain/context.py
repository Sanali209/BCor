"""ProcessingContext — carrier for asset processing pipeline config."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProcessingContext:
    """Carries configuration and state through the asset processing pipeline.

    A single ProcessingContext is created per field-recalculation event and
    passed to the selected handler. Handlers read from `metadata` for
    type-specific config (e.g. thumb size, OCR language, chunk size).

    Attributes:
        asset_id: The unique ID of the asset being processed.
        mime_type: MIME type of the asset (used for handler dispatch).
        uri: The asset's URI (local path, URL, etc.).
        field_name: The name of the Stored field being computed.
        metadata: Extra per-field configuration forwarded from Stored.context_metadata.
        session: Optional Neo4j session for graph-aware handlers.
    """

    asset_id: str
    mime_type: str
    uri: str
    field_name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    session: Any = None
