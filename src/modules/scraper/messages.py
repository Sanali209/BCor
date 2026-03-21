from src.core.messages import Command, Event
from .domain.interfaces import ScraperConfig, ScraperResult

class ScrapePageCommand(Command):
    config: ScraperConfig

class ScrapedEvent(Event):
    result: ScraperResult
