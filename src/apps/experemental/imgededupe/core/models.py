"""
Data Models Module.

Defines the core domain entities using Pydantic for validation and type safety.
Includes models for Files, Relations, and Clusters.
"""
from enum import Enum
from typing import List, Optional, Any, Dict
import os
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from src.core.domain import Aggregate
from pydantic.dataclasses import dataclass

class RelationType(str, Enum):
    """
    Enumeration of all possible relationship types between two files.
    """
    NEW_MATCH = 'new_match'           # Unreviewed match
    DUPLICATE = 'duplicate'           # Confirmed exact duplicate
    NEAR_DUPLICATE = 'near_duplicate' # very close, maybe compression artifacts
    CROP_DUPLICATE = 'crop_duplicate' # one is crop of another
    SIMILAR = 'similar'               # generic similar
    SIMILAR_STYLE = 'similar_style'   # style match
    SAME_PERSON = 'same_person'       # face match
    SAME_IMAGE_SET = 'same_image_set' # burst mode, etc.
    OTHER = 'other'                   # miscellaneous
    NOT_DUPLICATE = 'not_duplicate'   # Explicitly rejected

@dataclass
class FileAggregate(Aggregate):
    """
    Represents a file on disk as a domain aggregate.
    """
    path: str
    id: Optional[int] = None
    phash: Optional[str] = None
    file_size: int = 0
    size: int = 0
    width: int = 0
    height: int = 0
    last_modified: float = 0.0

    def __post_init__(self):
        super().__init__()

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

class FileRelation(BaseModel):
    id1: int
    id2: int
    relation_type: RelationType
    distance: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)

class Cluster(BaseModel):
    id: Optional[int] = None
    name: str
    target_folder: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class ClusterMember(BaseModel):
    cluster_id: int
    file_path: str
    added_at: datetime = Field(default_factory=datetime.now)

    @field_validator('file_path')
    @classmethod
    def normalize_path(cls, v: str) -> str:
        return os.path.normpath(v)
