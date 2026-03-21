"""ImageDedup use case: Scrape images.
"""
from __future__ import annotations

from typing import Any

from loguru import logger

from src.adapters.web.scraper_engine import ScraperEngine
from src.common.web.config import ScraperConfig
from src.core.unit_of_work import AbstractUnitOfWork


class ScrapeImagesUseCase:
    """Orchestrates image scraping and storage in ImageDedup."""

    def __init__(
        self,
        scraper: ScraperEngine,
        uow: AbstractUnitOfWork
    ) -> None:
        self.scraper = scraper
        self.uow = uow

    async def execute(self) -> int:
        """Run the scraper and add new images to the current project."""
        logger.info("Executing image scraping use case...")
        
        topics = await self.scraper.scrape_site()
        logger.info(f"Scraped {len(topics)} topics.")
        
        # In a real app, we would process topics here:
        # 1. Create ImageItem for each topic.
        # 2. Add to a specific ImageGroup in the project.
        # For now, we just count them as a demonstration.
        
        return len(topics)
