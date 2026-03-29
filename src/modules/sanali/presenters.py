import os
from typing import Optional, List
from loguru import logger
from .services import ProjectStateService, DuplicateService, NeiroFilterService, UserPreferenceService
from .domain import ProjectImageGroup, ProjectImageItem

class ImageDedupPresenter:
    """
    BCor-native Presenter for the Image Decuplication Application.
    Coordinates between services and provides a clean interface for the UI.
    """
    def __init__(
        self, 
        state_service: ProjectStateService, 
        dup_service: DuplicateService,
        neiro_service: NeiroFilterService,
        pref_service: UserPreferenceService
    ):
        self.state_service = state_service
        self.dup_service = dup_service
        self.neiro_service = neiro_service
        self.pref_service = pref_service

    async def load_project(self, project_path: str):
        """Load a project from the specified path."""
        logger.info(f"Loading project from: {project_path}")
        await self.state_service.load_from_path(project_path)

    async def save_project(self, project_path: Optional[str] = None):
        """Save the current project state."""
        logger.info(f"Saving project state...")
        await self.state_service.save_to_path(project_path)

    async def search_duplicates(self, threshold: float = 0.9):
        """Run deduplication process."""
        images = self.state_service.get_all_images()
        if not images:
            logger.warning("No images loaded.")
            return

        image_paths = [img.path for img in images]
        duplicate_groups = await self.dup_service.find_duplicates(image_paths, threshold)
        await self.state_service.update_groups(duplicate_groups)

    async def create_advision_list(self):
        """Create similar image list (Advision)."""
        logger.info("Creating Advision list...")
        images = self.state_service.get_all_images()
        if not images:
            return

        advision_groups = []
        for img in images:
            similar_items = await self.dup_service.find_similar(img.path, top_k=6)
            group = ProjectImageGroup(label=os.path.basename(img.path), items=[img] + similar_items)
            advision_groups.append(group)
            
        await self.state_service.update_groups(advision_groups)

    async def create_neiro_filter_list(self, model: str = "sanali209/nsfwfilter"):
        """Create groups based on AI tagging."""
        logger.info(f"Running NeiroFilter with model: {model}")
        images = self.state_service.get_all_images()
        if not images:
            return

        image_paths = [img.path for img in images]
        tagged_results = await self.neiro_service.tag_images(image_paths)
        
        new_groups = []
        for label, paths in tagged_results.items():
            items = [ProjectImageItem(path=p) for p in paths]
            new_groups.append(ProjectImageGroup(label=label, items=items))
            
        await self.state_service.update_groups(new_groups)

    def clear_selection(self):
        self.state_service.clear_all_selections()

    def get_groups(self) -> List[ProjectImageGroup]:
        return self.state_service.get_groups()
