from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID, uuid4

from src.core.domain import Aggregate

if TYPE_CHECKING:
    pass


@dataclass
class EntityType:
    """Type of entity involved in a relation (e.g., 'image', 'person', 'tag')."""
    code: str
    name: str


@dataclass
class RelationType:
    """Nature of the connection (e.g., 'contains', 'similar_to', 'depicts')."""
    code: str
    name: str
    is_bidirectional: bool = False


@dataclass(repr=False)
class Category(Aggregate):
    """Hierarchical classification for images."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    full_path: str = ""
    age_restriction: str = "G"
    parent_id: Optional[UUID] = None
    sort_order: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__init__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Category):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass(repr=False)
class Image(Aggregate):
    """Primary domain entity representing a gallery image."""
    id: UUID = field(default_factory=uuid4)
    file_path: str = ""
    title: str = ""
    description: str = ""
    uploaded_at: datetime = field(default_factory=datetime.now)
    uploaded_by_id: Optional[UUID] = None
    
    # Aggregated metrics for performance
    rating_sum: int = 0
    rating_count: int = 0
    
    # Processing status
    has_clip_vector: bool = False
    has_blip_vector: bool = False
    
    # Metadata
    md5_hash: Optional[str] = None
    content_type: str = "image/jpeg"
    size_bytes: int = 0
    
    # Collections
    category_ids: List[UUID] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        super().__init__()
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Image):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
    
    @property
    def rating(self) -> float:
        """Calculates average rating."""
        if self.rating_count == 0:
            return 0.0
        return self.rating_sum / self.rating_count


@dataclass
class RelationRecord:
    """A link between two entities with potential confidence score."""
    id: UUID = field(default_factory=uuid4)
    from_entity_type: str = ""
    from_id: str = ""  # ID as string to support heterogeneous entities
    to_entity_type: str = ""
    to_id: str = ""
    relation_type_code: str = ""
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Detection:
    """An object or face detected within an image."""
    id: UUID = field(default_factory=uuid4)
    image_id: UUID = field(default_factory=uuid4)
    label: str = ""
    box_2d: List[float] = field(default_factory=list)  # [x1, y1, x2, y2]
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorRecord:
    """Reference to a vector stored in the vector database."""
    id: UUID = field(default_factory=uuid4)
    image_id: UUID = field(default_factory=uuid4)
    model_name: str = ""  # 'clip', 'blip', etc.
    collection_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
