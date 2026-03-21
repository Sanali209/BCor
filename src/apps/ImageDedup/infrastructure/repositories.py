from __future__ import annotations

import os

from ..domain.project import ImageDedupProject


class JsonProjectRepository:
    """Persistence for ImageDedupProject using JSON files."""

    def __init__(self, base_path: str) -> None:
        self.base_path = base_path
        self.seen: set[ImageDedupProject] = set()

    async def get(self, project_id: str) -> ImageDedupProject:
        """Load or create a project by ID.
        
        Currently assumes the project ID is just a label and works in base_path.
        """
        project = ImageDedupProject(project_id=project_id, work_path=self.base_path)
        
        load_path = os.path.join(self.base_path, "groupList.json")
        if os.path.exists(load_path):
            with open(load_path, encoding="utf-8") as f:
                raw = f.read()
            groups = ImageDedupProject.groups_from_json(raw)
            project.load_groups(groups)
        
        self.seen.add(project)
        return project

    async def save(self, project: ImageDedupProject) -> None:
        """Save project state to disk."""
        save_path = os.path.join(self.base_path, "groupList.json")
        os.makedirs(self.base_path, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(project.to_json())
        self.seen.add(project)
