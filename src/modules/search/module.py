from src.core.module import BaseModule
from .provider import SearchProvider
from .messages import SearchImagesCommand
from .handlers import search_images_handler

class SearchModule(BaseModule):
    """Module for web and image search capabilities."""
    
    def __init__(self):
        super().__init__()
        self.provider = SearchProvider()
        self.command_handlers = {
            SearchImagesCommand: search_images_handler,
        }
