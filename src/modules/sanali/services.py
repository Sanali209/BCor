import os
import sys
import asyncio
import uuid
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from loguru import logger
from src.common.paths import PathNormalizer
from diskcache import Cache
from .domain import ProjectImageGroup, ProjectImageItem
from src.apps.experemental.sanali.Python.core_apps.services.configuration_service import ConfigurationService as LegacyConfig

class ConfigurationService(LegacyConfig):
    """BCor-native version of the ConfigurationService, inheriting from legacy for bridge compatibility"""
    def __init__(self):
        super().__init__()
        self.default_job_name = "rating_competition"
        self.initial_rating_min = 1
        self.initial_rating_max = 10
        logger.info("BCor Configuration Service initialized")

    def get_choices_list(self):
        return [str(i) for i in range(self.initial_rating_min, self.initial_rating_max + 1)]


class DuplicateService:
    """BCor-native service for finding duplicate images using legacy CNN logic."""
    
    def __init__(self):
        # Setup legacy path
        self.legacy_root = os.path.abspath("src/apps/experemental/sanali/Python")
        if self.legacy_root not in sys.path:
            sys.path.append(self.legacy_root)
        self.finder = None # Initialize finder
            
    @PathNormalizer.normalize_args('image_paths')
    async def find_duplicates(self, image_paths: List[str], threshold: float = 0.9) -> List[Any]:
        """
        Modern interface for finding duplicates using the consolidated service.
        """
        try:
            from SLM.vision.imagetotensor.CNN_Finder import CNN_Dub_Finder
            if not self.finder:
                # First use, initialize index
                self.finder = CNN_Dub_Finder()
                # BuildIndex expects a list of paths
                await asyncio.get_running_loop().run_in_executor(None, self.finder.BuildIndex, image_paths)
            
            # FindDubs returns a list of lists of paths
            clusters = await asyncio.get_running_loop().run_in_executor(None, self.finder.FindDubs, image_paths, threshold)
            
            result_groups = []
            for i, cluster in enumerate(clusters):
                group_items = [ProjectImageItem(path=p) for p in cluster]
                result_groups.append(ProjectImageGroup(label=f"cluster_{i}", items=group_items))
            return result_groups
        except Exception as e:
            logger.error(f"Error in DuplicateService.find_duplicates: {e}")
            return []

    @PathNormalizer.normalize_args('image_path')
    async def find_similar(self, image_path: str, top_k: int = 6) -> List[ProjectImageItem]:
        """
        Advision implementation using modern DuplicateService.
        """
        try:
            from SLM.vision.dubFileHelper import DuplicateFindHelper
            if not self.finder:
                # If finder is not initialized, we can't find similar.
                # In a real app, BuildIndex would be called earlier or on demand.
                logger.warning("DuplicateService.finder not initialized. Cannot find similar images.")
                return []
            
            # FindTopSimilar returns [query_path, sim1, sim2, ...]
            similar_paths = await asyncio.get_running_loop().run_in_executor(None, self.finder.FindTopSimilar, image_path, top_k)
            # FindTopSimilar returns [query_path, sim1, sim2, ...]
            return [ProjectImageItem(path=p) for p in similar_paths[1:]]
        except Exception as e:
            logger.error(f"Error in DuplicateService.find_similar: {e}")
            return []


class ProjectStateService:
    """BCor-native service for managing project state (groups/images)."""
    
    def __init__(self):
        self.groups: List[ProjectImageGroup] = []
        self.project_path: Optional[str] = None

    async def load_from_path(self, path: str):
        self.project_path = path
        logger.info(f"ProjectStateService: Loaded from {path}")

    async def save_to_path(self, path: Optional[str] = None):
        target_path = path or self.project_path
        if not target_path:
            raise ValueError("No project path specified for saving.")
        logger.info(f"ProjectStateService: Saved to {target_path}")

    def get_groups(self) -> List[ProjectImageGroup]:
        return self.groups

    def get_all_images(self) -> List[ProjectImageItem]:
        all_images = []
        for group in self.groups:
            all_images.extend(group.items)
        return all_images

    async def update_groups(self, new_groups: List[ProjectImageGroup]):
        self.groups = new_groups

    def add_group(self, group: ProjectImageGroup):
        self.groups.append(group)

    def clear_all_selections(self):
        for group in self.groups:
            group.selected = False
            for img in group.items:
                img.selected = False


class NeiroFilterService:
    """Service for AI-based image tagging and filtering."""
    
    def __init__(self, model_name: str = "sanali209/nsfwfilter"):
        self.model_name = model_name
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            try:
                from transformers import pipeline
                self._pipeline = pipeline(model=self.model_name)
            except ImportError:
                logger.error("transformers library not found. NeiroFilterService disabled.")
                raise
        return self._pipeline

    async def tag_images(self, image_paths: List[str]) -> Dict[str, List[str]]:
        """Tag a list of images and return a mapping of label -> [paths]."""
        pipe = self._get_pipeline()
        results = {}
        # In a real app, this would be batched and run in an executor
        loop = asyncio.get_running_loop()
        
        def run_pipe():
            mapping = {}
            for path in image_paths:
                try:
                    res = pipe(path)
                    label = res[0]['label']
                    mapping.setdefault(label, []).append(path)
                except Exception as e:
                    logger.warning(f"Failed to tag {path}: {e}")
            return mapping

        return await loop.run_in_executor(None, run_pipe)


class UserPreferenceService:
    """Service for managing user preferences and project-specific caches."""
    
    def __init__(self, cache_path: str = r"D:\data\ImSortPrCache"):
        self.cache = Cache(cache_path)

    @PathNormalizer.normalize_args('path1', 'path2')
    def add_hidden_pair(self, path1: str, path2: str):
        pairs = self.cache.get("hidden_pairs", [])
        pair = tuple(sorted([path1, path2]))
        if pair not in pairs:
            pairs.append(pair)
            self.cache.set("hidden_pairs", pairs)
            logger.info(f"Added hidden pair: {pair}")

    def get_hidden_pairs(self) -> List[tuple]:
        return self.cache.get("hidden_pairs", [])

    @PathNormalizer.normalize_args('folder_path')
    def add_imageset_folder(self, folder_path: str):
        folders = self.cache.get("imageset_folders", [])
        if folder_path not in folders:
            folders.append(folder_path)
            self.cache.set("imageset_folders", folders)
            logger.info(f"Added imageset folder: {folder_path}")

    def get_imageset_folders(self) -> List[str]:
        return self.cache.get('imageset_folders', default=[])

    def close(self):
        """Close the underlying cache to prevent resource leaks."""
        self.cache.close()
        logger.debug("UserPreferenceService cache closed")
