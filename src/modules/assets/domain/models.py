"""Domain models for the Assets module.

All models use AGM metadata annotations (@Rel, @Stored) for graph persistence.
Polymorphic loading is enabled via register_subclass in AssetsModule.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any, Optional

from src.modules.agm.metadata import Rel, RelMetadata, Stored, Unique, Indexed, VectorIndex, OnComplete
from src.modules.agm.ui_metadata import Column, DisplayName, Hidden, IsThumbnail, Searchable

if TYPE_CHECKING:
    pass


# ─── Core Asset Hierarchy ─────────────────────────────────────────────────────

@dataclass
class SimilarTo:
    """Metadata for SIMILAR relationship properties."""
    score: float = 0.0
    engine: str = ""


@dataclass
class Asset:
    """Base class for all assets — digital and physical.

    Fields:
        id:           Unique identifier (UUID or generated).
        uri:          Universal Resource Identifier — primary key in the graph.
                      Schemes: file://, https://, yt://, physical://...
        name:         Human-readable name.
        mime_type:    MIME type (auto-detected or provided).
        description:  Free-form description.
        content_hash: SHA256 of raw content.
        size:         Size in bytes.
    """

    id: Annotated[str, Unique(), Hidden()]
    uri: Annotated[str, Indexed(), DisplayName("Source URI"), Column(width=300), Searchable(priority=5)]
    name: Annotated[str, DisplayName("Name"), Column(width=200), Searchable(priority=1)] = ""
    mime_type: Annotated[str, DisplayName("MIME Type"), Column(width=100), Searchable(priority=2)] = ""
    description: Annotated[str, DisplayName("Description"), Column(width=250), Searchable(priority=10)] = ""
    content_hash: Annotated[
        str,
        Indexed(),
        DisplayName("Hash"),
        Column(width=150),
        Stored(source_field="uri", handler="ContentHashHandler", use_taskiq=True, priority=1),
    ] = ""
    size: Annotated[int, DisplayName("Size (Bytes)"), Column(width=100), Searchable(priority=3, widget="range")] = 0
    thumbnails_ready: Annotated[
        bool,
        Stored(source_fields=["uri", "content_hash"], handler="ThumbnailHandler", use_taskiq=True, priority=5),
    ] = False
    embedding: Annotated[
        list[float],
        Stored(source_field="description", mime_scope="*/*", use_taskiq=True, priority=10),
        VectorIndex(dims=384)
    ] = field(default_factory=list)
    tags: Annotated[
        list["Tag"],
        Rel(type="HAS_TAG"),
    ] = field(default_factory=list)
    annotations: Annotated[
        list["Annotation"],
        Rel(type="HAS_ANNOTATION"),
    ] = field(default_factory=list)
    chunks: Annotated[
        list["ContentChunk"],
        Rel(type="HAS_CHUNK"),
    ] = field(default_factory=list)
    similar: Annotated[
        list["SimilarTo"],
        Rel(type="SIMILAR", metadata=RelMetadata(SimilarTo)),
        Hidden()
    ] = field(default_factory=list)
    inference_events: Annotated[
        list["InferenceEvent"],
        Rel(type="HAS_INFERENCE"),
        Hidden()
    ] = field(default_factory=list)


@dataclass
class Tag:
    """A hierarchical classification label."""
    id: Annotated[str, Unique()]
    name: Annotated[str, Indexed()]
    description: str = ""
    parent: Annotated[Optional["Tag"], Rel(type="CHILD_OF")] = None


@dataclass
class Annotation:
    """Base annotation node linked to an Asset."""
    id: Annotated[str, Unique()]
    asset_id: Annotated[str, Indexed()]
    annotator: str
    confidence: float
    created_at: float


@dataclass
class InferenceEvent(Annotation):
    """Event tracking the execution and outcome of an AI/Processing handler."""
    handler_name: str
    field_name: str
    model_name: str | None = None
    status: str = "PENDING"  # PENDING, SUCCESS, ERROR
    error_message: str | None = None
    created_at_str: Annotated[str | None, Indexed(), DisplayName("Timestamp")] = None
    target_label_name: str = "InferenceEvent"


@dataclass
class CaptionAnnotation(Annotation):
    """Generated text caption for an asset (CLIP/BLIP/Ollama)."""
    text: str
    model_name: str | None = None


@dataclass
class SingleLabelAnnotation(Annotation):
    """Assigns a single classification label to an asset."""
    label: str


@dataclass
class MultiLabelAnnotation(Annotation):
    """Assigns multiple classification labels to an asset."""
    labels: list[str] = field(default_factory=list)


@dataclass
class PolygonAnnotation(Annotation):
    """Assigns a polygonal region within an asset to a label."""
    class_label: str
    points: list[list[float]] = field(default_factory=list)


@dataclass
class BoundingBoxAnnotation(Annotation):
    """Detects and localizes an object within an asset (image/video)."""
    class_label: str
    x: float
    y: float
    w: float
    h: float


@dataclass
class ImageAsset(Asset):
    """Asset representing a digital image."""
    width: int = 0
    height: int = 0
    format: str = ""
    phash: Annotated[str, Indexed()] = ""
    
    # EXIF/Metadata fields
    f_number: Annotated[float, DisplayName("F-Number"), Stored(source_field="uri", handler="Pyexiv2Smart"), Searchable(priority=20, widget="range")] = 0.0
    exposure_time: Annotated[float, DisplayName("Exposure"), Stored(source_field="uri", handler="Pyexiv2Smart"), Searchable(priority=21, widget="range")] = 0.0
    iso: Annotated[int, DisplayName("ISO"), Stored(source_field="uri", handler="Pyexiv2Smart"), Searchable(priority=22, widget="range")] = 0
    camera_make: Annotated[str, DisplayName("Camera Make"), Stored(source_field="uri", handler="Pyexiv2Smart"), Searchable(priority=23)] = ""
    camera_model: Annotated[str, DisplayName("Camera Model"), Stored(source_field="uri", handler="Pyexiv2Smart"), Searchable(priority=24)] = ""
    captured_at: Annotated[float, DisplayName("Captured At"), Stored(source_field="uri", handler="Pyexiv2Smart"), Searchable(priority=25, widget="date")] = 0.0
    
    # Embeddings
    clip_embedding: Annotated[
        list[float],
        Stored(source_fields=["uri"], mime_scope="image/*", handler="CLIP", use_taskiq=True, priority=15),
        VectorIndex(dims=512)
    ] = field(default_factory=list)
    blip_embedding: Annotated[
        list[float],
        Stored(source_fields=["uri"], mime_scope="image/*", handler="BLIP", use_taskiq=True, priority=15),
        VectorIndex(dims=768)
    ] = field(default_factory=list)
    wd_tags: Annotated[
        list[Tag],
        Rel(type="HAS_WD_TAG"),
        Stored(source_fields=["uri"], mime_scope="image/*", handler="SmilingWolfHandler", use_taskiq=True, priority=10),
    ] = field(default_factory=list)


@dataclass
class VideoAsset(Asset):
    """Asset representing a video file."""
    duration: float = 0.0
    fps: float = 0.0
    codec: str = ""


@dataclass
class AudioAsset(Asset):
    """Asset representing an audio file."""
    duration: float = 0.0
    samplerate: int = 0
    channels: int = 1


@dataclass
class TextAsset(Asset):
    """Asset representing a text-based document."""
    language: str = "en"
    word_count: int = 0


@dataclass
class PhysicalAsset(Asset):
    """Asset representing a physical object."""
    serial_number: str = ""
    location: str = ""


@dataclass
class ContentChunk:
    """A text chunk created from a parent Asset's content (for RAG)."""
    id: Annotated[str, Unique()]
    asset_id: Annotated[str, Indexed()]
    content: str
    chunk_index: int = 0
    embedding: Annotated[
        list[float],
        Stored(source_field="content", mime_scope="*/*", use_taskiq=True, priority=10),
        VectorIndex(dims=384)
    ] = field(default_factory=list)


@dataclass
class Product:
    """Domain entity for a Product."""
    id: Annotated[str, Unique()]
    name: Annotated[str, Indexed()]
    description: str = ""
    assets: Annotated[list[Asset], Rel(type="HAS_ASSET")] = field(default_factory=list)


@dataclass
class Project:
    """Domain entity for a Project."""
    id: Annotated[str, Unique()]
    name: Annotated[str, Indexed()]
    products: Annotated[list[Product], Rel(type="INCLUDES_PRODUCT")] = field(default_factory=list)


class RelationType(str, Enum):
    """Semantic relationship types between two assets."""
    NEW_MATCH = "NEW_MATCH"
    DUPLICATE = "DUPLICATE"
    NEAR_DUPLICATE = "NEAR_DUPLICATE"
    CROP_DUPLICATE = "CROP_DUPLICATE"
    SIMILAR_STYLE = "SIMILAR_STYLE"
