from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Stored:
    """Metadata to mark a field for background recalculation.

    Supports single or multi-source trigger fields, MIME-scoped dispatch,
    and per-field handler configuration via explicit names or context_metadata.

    Attributes:
        source_field: Single trigger field (backward compatible).
        source_fields: List of trigger fields — event fires if ANY changes.
            Mutually exclusive with source_field.
        mime_scope: MIME pattern for handler dispatch (e.g. 'image/*', '*/*').
        handler: Explicitly named processor (e.g., "SmilingWolf", "Piexif").
        model: Specific model name for the handler (e.g., "wd-vit-tagger-v3").
        use_taskiq: If True, offload this computation to a background worker.
        priority: Task priority (0 = low, 10 = high).
        context_metadata: Extra config forwarded to the processing handler.
        fusion_params: Configuration for combining results from multiple models.
    """

    source_field: str | None = None
    source_fields: tuple[str, ...] | None = None
    depends_on: tuple[str, ...] = field(default_factory=tuple)
    mime_scope: str | None = None
    handler: str | None = None
    model: str | None = None
    use_taskiq: bool = False
    priority: int = 0
    context_metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    fusion_params: tuple[tuple[str, Any], ...] | None = None

    def __post_init__(self):
        # 1. Validation
        if self.source_field is None and self.source_fields is None:
            raise ValueError(
                "Stored requires either 'source_field' or 'source_fields'."
            )
        if self.source_field is not None and self.source_fields is not None:
            raise ValueError(
                "Stored accepts 'source_field' OR 'source_fields', not both."
            )

        # 2. Immutable Coercion (for Hashing)
        # Using object.__setattr__ because the dataclass is frozen
        if self.source_fields is not None and isinstance(self.source_fields, list):
            object.__setattr__(self, "source_fields", tuple(self.source_fields))
        
        if self.context_metadata is not None and isinstance(self.context_metadata, dict):
            # Sort keys to ensure stable hash
            sorted_items = tuple(sorted(self.context_metadata.items()))
            object.__setattr__(self, "context_metadata", sorted_items)
            
        if self.fusion_params is not None and isinstance(self.fusion_params, dict):
            # Sort keys to ensure stable hash
            sorted_items = tuple(sorted(self.fusion_params.items()))
            object.__setattr__(self, "fusion_params", sorted_items)

    def effective_source_fields(self) -> list[str]:
        """Returns the unified list of trigger field names."""
        if self.source_fields is not None:
            return list(self.source_fields)
        return [self.source_field]  # type: ignore[list-item]

    @property
    def context_metadata_dict(self) -> dict[str, Any]:
        """Returns context_metadata as a dictionary."""
        return dict(self.context_metadata)

    @property
    def fusion_params_dict(self) -> dict[str, Any] | None:
        """Returns fusion_params as a dictionary."""
        if self.fusion_params is None:
            return None
        return dict(self.fusion_params)


@dataclass(frozen=True)
class Live:
    """Metadata to mark a field for live hydration via DI.

    Attributes:
        handler: The type to resolve from the container to populate
            this field.
    """

    handler: Any


@dataclass(frozen=True)
class RelMetadata:
    """Metadata for properties stored on graph relationships (edges)."""

    model: type | None = None


@dataclass(frozen=True)
class Rel:
    """Metadata to define graph relationships.

    Attributes:
        type: The Neo4j relationship type (e.g., 'WORKS_IN').
        direction: The relationship direction (OUTGOING or INCOMING).
        metadata: Optional class defining relationship properties.
    """

    type: str
    direction: str = "OUTGOING"  # OUTGOING or INCOMING
    metadata: RelMetadata | None = None


@dataclass(frozen=True)
class Unique:
    """Metadata to mark a field as unique in the graph."""
    pass


@dataclass(frozen=True)
class Indexed:
    """Metadata to mark a field for standard indexing (Range index)."""
    pass


@dataclass(frozen=True)
class VectorIndex:
    """Metadata to mark a field for vector indexing.

    Attributes:
        dims: Vector dimensions (e.g. 384, 1536).
        metric: Similarity metric ('cosine', 'euclidean', 'overlap').
    """
    dims: int
    metric: str = "cosine"
    index_name: str | None = None


@dataclass(frozen=True)
class OnComplete:
    """Metadata to declare an action to run when specified fields are ready.

    Usually attached to a dummy field on the domain model to serve as a class-level
    declarative hook.

    Attributes:
        depends_on: List of fields that must be non-empty/completed.
        handler: The name of the action handler to invoke (resolved via DI).
        use_taskiq: If True, execute the action asynchronously in a background worker.
        priority: Task priority.
    """
    depends_on: tuple[str, ...]
    handler: str
    use_taskiq: bool = True
    priority: int = 10


import typing


def get_field_metadata(cls: type, field_name: str) -> list[Any]:
    """Extracts all AGM metadata objects from a field's Annotated type."""
    try:
        hints = typing.get_type_hints(cls, include_extras=True)
        if field_name not in hints:
            # Fallback for inherited fields not yet in hints
            return []
        
        hint = hints[field_name]
        if typing.get_origin(hint) is typing.Annotated:
            return list(typing.get_args(hint)[1:])
        return []
    except Exception:
        return []


def resolve_relation_type(cls: type, field_name: str) -> str | None:
    """Finds the Neo4j relationship type defined via @Rel for a field."""
    metadata = get_field_metadata(cls, field_name)
    for item in metadata:
        if isinstance(item, Rel):
            return item.type
    return None
