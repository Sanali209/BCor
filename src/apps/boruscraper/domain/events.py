from dataclasses import dataclass
from typing import Optional, List
from src.core.messages import Event

@dataclass
class ProjectStartedEvent(Event):
    project_id: int

@dataclass
class ProjectPausedEvent(Event):
    project_id: int

@dataclass
class PostDiscoveredEvent(Event):
    project_id: int
    post_id: str
    topic_url: str

@dataclass
class ResourceDownloadedEvent(Event):
    project_id: int
    post_id: str
    relative_path: str
    dhash: Optional[str] = None
    
@dataclass
class DuplicateFoundEvent(Event):
    project_id: int
    absolute_path: str
    conflicts: list
    dhash: str
