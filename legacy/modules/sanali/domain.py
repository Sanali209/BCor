import uuid
from dataclasses import dataclass, field
from typing import List

@dataclass
class DuplicateItem:
    path: str
    distance: float = 0.0

@dataclass
class DuplicateGroup:
    path: str
    results: List[DuplicateItem] = field(default_factory=list)
    none_tensor: bool = False

@dataclass
class ProjectImageItem:
    path: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    score: float = 0.0
    selected: bool = False

@dataclass
class ProjectImageGroup:
    label: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    items: List[ProjectImageItem] = field(default_factory=list)
    selected: bool = False
    expanded: bool = True
    propositions: List[ProjectImageItem] = field(default_factory=list)
