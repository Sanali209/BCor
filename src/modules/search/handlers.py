from typing import List
from src.core.messagebus import MessageBus
from .domain.interfaces import ISearchAdapter, SearchResult
from .messages import SearchImagesCommand, SearchResultsEvent

async def search_images_handler(
    command: SearchImagesCommand,
    adapters: list[ISearchAdapter],
    event_bus: MessageBus
) -> SearchResultsEvent:
    """Orchestrates multi-provider image search."""
    all_results = []
    
    # Simple strategy: try all adapters and combine
    for adapter in adapters:
        try:
            results = await adapter.search_images(command.query, limit=command.limit)
            all_results.extend(results)
        except Exception as e:
            from loguru import logger
            logger.error(f"Search adapter {type(adapter).__name__} failed: {e}")
            
    # Deduplicate or sort if needed
    
    event = SearchResultsEvent(query=command.query, results=all_results)
    await event_bus.dispatch(event)
    return event
