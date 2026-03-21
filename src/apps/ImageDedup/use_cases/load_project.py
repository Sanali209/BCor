from __future__ import annotations
import os
import uuid
from loguru import logger
from ..domain.project import ImageDedupProject
from ..core.repositories.file_repository import FileRepository
from ..messages import ProjectLoadedEvent

class LoadProjectUseCase:
    """BCor Use Case to load a dedup project.
    
    This replaces direct loading logic from the legacy GUI.
    """
    def __init__(self, file_repo: FileRepository):
        self._file_repo = file_repo

    async def execute(self, work_path: str) -> ProjectLoadedEvent:
        """Loads or initializes a project for the given path."""
        logger.info(f"Loading ImageDedup project for path: {work_path}")
        
        # In legacy, we might load from a JSON file or DB
        # For now, let's create an aggregate and fire an event
        # If there's a JSON, we'd use project.groups_from_json()
        
        project = ImageDedupProject(
            project_id=str(uuid.uuid4()),
            work_path=work_path,
        )
        
        # Load existing groups if they exist (legacy bit)
        json_path = os.path.join(work_path, "groupList.json")
        if os.path.exists(json_path):
             with open(json_path, 'r', encoding='utf-8') as f:
                 groups = project.groups_from_json(f.read())
                 project.load_groups(groups)
        
        event = ProjectLoadedEvent(
            project_id=project.project_id,
            work_path=project.work_path,
            group_count=len(project.groups)
        )
        
        # In a full BCor system, we might add this event to the project.events
        # and let the MessageBus pick it up via UoW. 
        # But for Strangler mode, we just return the event for now.
        return event
