from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID
from src.core.messages import Command


@dataclass
class UploadImage(Command):
    file_path: str
    title: str = ""
    description: str = ""
    category_ids: List[UUID] = field(default_factory=list)


@dataclass
class UpdateImageMetadata(Command):
    image_id: UUID
    title: Optional[str] = None
    description: Optional[str] = None
    category_ids: Optional[List[UUID]] = None


@dataclass
class AssignCategories(Command):
    image_ids: List[UUID]
    category_ids: List[UUID]
    mode: str = "add"  # 'add' or 'replace'


@dataclass
class CreateRelation(Command):
    from_id: str
    from_type: str
    to_id: str
    to_type: str
    relation_type: str
    confidence: float = 1.0


@dataclass
class RunAiScan(Command):
    image_id: UUID


@dataclass
class BulkAssignCategories(Command):
    image_ids: list[UUID]
    category_ids: list[UUID]


@dataclass
class BulkCreateRelations(Command):
    from_ids: list[str]
    from_type: str
    to_id: str
    to_type: str
    relation_type: str
    scan_types: List[str] = field(default_factory=lambda: ["clip", "blip", "objects"])


@dataclass
class SearchByImage(Command):
    file_path: str
    threshold: float = 0.7
    limit: int = 20
