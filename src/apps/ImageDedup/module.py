"""ImageDedup module registration."""
from __future__ import annotations

from src.apps.ImageDedup.messages import (
    FindDuplicatesCommand,
    LaunchImageDedupCommand,
    LoadProjectCommand,
    SaveProjectCommand,
    TagImagesCommand,
)
from src.core.module import BaseModule


class ImageDedupModule(BaseModule):
    """Module integrating the ImageDedup app into the BCor system."""

    name = "image_dedup"

    def __init__(self) -> None:
        super().__init__()
        from src.apps.ImageDedup.provider import ImageDedupProvider
        self.provider = ImageDedupProvider()

    def setup(self) -> None:
        from src.apps.ImageDedup import handlers

        self.command_handlers[LaunchImageDedupCommand] = handlers.launch_image_dedup_handler
        self.command_handlers[FindDuplicatesCommand] = handlers.find_duplicates_handler
        self.command_handlers[SaveProjectCommand] = handlers.save_project_handler
        self.command_handlers[LoadProjectCommand] = handlers.load_project_handler
        self.command_handlers[TagImagesCommand] = handlers.tag_images_handler
