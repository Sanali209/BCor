"""
Data Models Module.

Defines the core domain entities using Pydantic for validation and type safety.
Includes models for Files, Relations, and Clusters.
"""
from enum import Enum
from typing import List, Optional, Any, Dict
import os
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
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

class FileAggregate(Aggregate):
    """
    Represents a file on disk as a domain aggregate.
    """
    def __init__(
        self, 
        path: str, 
        id: Optional[int] = None, 
        phash: Optional[str] = None, 
        file_size: int = 0,
        size: int = 0,
        width: int = 0,
        height: int = 0,
        last_modified: float = 0.0
    ):
        super().__init__()
        self.path = path
        self.id = id
        self.phash = phash
        self.file_size = file_size
        self.size = size or file_size
        self.width = width
        self.height = height
        self.last_modified = last_modified

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

class FileRelation(BaseModel):
    id1: int
    id2: int
    relation_type: RelationType
    distance: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def is_visible(self) -> bool:
        """Determines if the relation should be shown in the 'Pending' view."""
        return self.relation_type == RelationType.NEW_MATCH

    @field_validator('id1', 'id2', mode='after')
    @classmethod
    def check_id_order(cls, v: int, info) -> int:
        # We can't easily sort in a single field validator without knowing both.
        # But we can use a model_validator or just sort in init.
        return v
    
    @model_validator(mode='after')
    def sort_ids(self) -> 'FileRelation':
        if self.id1 > self.id2:
            self.id1, self.id2 = self.id2, self.id1
        return self

class Cluster(Aggregate):
    """
    Represents a cluster (group) of duplicate files.
    """
    def __init__(
        self, 
        name: str, 
        id: Optional[int] = None, 
        target_folder: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        super().__init__()
        self.id = id
        self.name = name
        self.target_folder = target_folder
        self.created_at = created_at or datetime.now()

class ClusterMember(BaseModel):
    cluster_id: int
    file_path: str
    added_at: datetime = Field(default_factory=datetime.now)

    @field_validator('file_path')
    @classmethod
    def normalize_path(cls, v: str) -> str:
        return os.path.normpath(v)
