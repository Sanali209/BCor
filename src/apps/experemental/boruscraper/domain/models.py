import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from src.core.domain import Aggregate
from src.apps.experemental.boruscraper.domain.events import (
    ProjectStartedEvent, ProjectPausedEvent, 
    PostDiscoveredEvent, ResourceDownloadedEvent,
    DuplicateFoundEvent
)

@dataclass
class Resource:
    relative_path: str
    dhash: Optional[str] = None
    md5: Optional[str] = None

@dataclass
class Post:
    id: str
    project_id: int
    url: str
    data: Dict[str, Any] = field(default_factory=dict)
    resources: List[Resource] = field(default_factory=list)
    
    def add_resource(self, res: Resource):
        self.resources.append(res)

class Project(Aggregate):
    def __init__(self, id: int, name: str, settings: dict, start_urls: list, status: str = "queued"):
        super().__init__()
        self.id = id
        self.name = name
        self.settings = settings
        self.start_urls = start_urls
        self.status = status
        
    def start(self):
        if self.status != "running":
            self.status = "running"
            self.add_event(ProjectStartedEvent(self.id))
            
    def pause(self):
        if self.status == "running":
            self.status = "paused"
            self.add_event(ProjectPausedEvent(self.id))
            
    def reset(self):
        self.status = "queued"

    def mark_error(self):
        self.status = "error"

    def record_post_discovered(self, post_id: str, topic_url: str):
        self.add_event(PostDiscoveredEvent(self.id, post_id, topic_url))

    def record_resource_downloaded(self, post_id: str, relative_path: str, dhash: Optional[str] = None):
        self.add_event(ResourceDownloadedEvent(self.id, post_id, relative_path, dhash))
        
    def record_duplicate(self, absolute_path: str, conflicts: list, dhash: str):
        self.add_event(DuplicateFoundEvent(self.id, absolute_path, conflicts, dhash))

    def cycle_start_url(self, start_url: str):
        """Move the current start URL to the end of the queue."""
        if start_url in self.start_urls:
            self.start_urls.remove(start_url)
            self.start_urls.append(start_url)
