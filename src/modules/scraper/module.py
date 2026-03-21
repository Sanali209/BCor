from src.core.module import BaseModule
from .provider import ScraperProvider
from .messages import ScrapePageCommand
from .handlers import scrape_page_handler

class ScraperModule(BaseModule):
    def __init__(self):
        self.provider = ScraperProvider()
        self.command_handlers = {
            ScrapePageCommand: scrape_page_handler
        }
