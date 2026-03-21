from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Table, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import registry

from ..domain.entities import Category, Image, RelationRecord, Detection

mapper_registry = registry()

categories = Table(
    "gallery_categories",
    mapper_registry.metadata,
    Column("id", PG_UUID(as_uuid=True), primary_key=True),
    Column("name", String(255), nullable=False),
    Column("slug", String(255), nullable=False, unique=True),
    Column("full_path", String(1024), nullable=False),
    Column("age_restriction", String(10), default="G"),
    Column("parent_id", PG_UUID(as_uuid=True), ForeignKey("gallery_categories.id"), nullable=True),
    Column("sort_order", Integer, default=0),
    Column("metadata", JSON, default=dict),
)

images = Table(
    "gallery_images",
    mapper_registry.metadata,
    Column("id", PG_UUID(as_uuid=True), primary_key=True),
    Column("file_path", String(1024), nullable=False),
    Column("title", String(255)),
    Column("description", String),
    Column("uploaded_at", DateTime, nullable=False),
    Column("uploaded_by_id", PG_UUID(as_uuid=True), nullable=True),
    Column("rating_sum", Integer, default=0),
    Column("rating_count", Integer, default=0),
    Column("has_clip_vector", Boolean, default=False),
    Column("has_blip_vector", Boolean, default=False),
    Column("md5_hash", String(32)),
    Column("content_type", String(100)),
    Column("size_bytes", Integer, default=0),
    Column("category_ids", JSON, default=list),
)

relations = Table(
    "gallery_relations",
    mapper_registry.metadata,
    Column("id", PG_UUID(as_uuid=True), primary_key=True),
    Column("from_entity_type", String(50), nullable=False),
    Column("from_id", String(255), nullable=False),
    Column("to_entity_type", String(50), nullable=False),
    Column("to_id", String(255), nullable=False),
    Column("relation_type_code", String(50), nullable=False),
    Column("confidence", Float, default=1.0),
    Column("metadata", JSON, default=dict),
    Column("created_at", DateTime, nullable=False),
)

detections = Table(
    "gallery_detections",
    mapper_registry.metadata,
    Column("id", PG_UUID(as_uuid=True), primary_key=True),
    Column("image_id", PG_UUID(as_uuid=True), ForeignKey("gallery_images.id"), nullable=False),
    Column("label", String(100), nullable=False),
    Column("box_2d", JSON),
    Column("confidence", Float),
    Column("metadata", JSON, default=dict),
)


def start_mappers() -> None:
    """Configures imperative mapping for gallery entities."""
    mapper_registry.map_imperatively(Category, categories)
    mapper_registry.map_imperatively(Image, images)
    mapper_registry.map_imperatively(RelationRecord, relations)
    mapper_registry.map_imperatively(Detection, detections)
