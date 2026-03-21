from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
from src.core.messages import Event


@dataclass
class ImageUploaded(Event):
    image_id: UUID
    file_path: str


@dataclass
class ImageAnalyzed(Event):
    image_id: UUID
    tags: list[str]
    rating: str


@dataclass
class RelationCreated(Event):
    relation_id: UUID
    from_id: str
    to_id: str
    relation_type: str
