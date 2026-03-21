from src.core.messagebus import MessageBus
from .domain.interfaces import IScraperAdapter
from .messages import ScrapePageCommand, ScrapedEvent

async def scrape_page_handler(
    command: ScrapePageCommand,
    adapter: IScraperAdapter,
    event_bus: MessageBus
) -> ScrapedEvent:
    """Handles page scraping command."""
    result = await adapter.scrape_page(command.config)
    event = ScrapedEvent(result=result)
    await event_bus.dispatch(event)
    return event
