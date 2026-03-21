"""Web adapter: Modern scraping engine.

Orchestrates IBrowser and IExtractor to scrape sites based on ScraperConfig.
"""
from __future__ import annotations

import urllib.parse

from loguru import logger

from src.adapters.web.resource_downloader import ResourceDownloader
from src.common.web.config import ScraperConfig
from src.common.web.topic import TopicData
from src.core.web.i_browser import IBrowser
from src.core.web.i_extractor import IExtractor


class ScraperEngine:
    """BCor-native scraping engine."""

    def __init__(
        self,
        browser: IBrowser,
        extractor: IExtractor,
        downloader: ResourceDownloader,
        config: ScraperConfig
    ) -> None:
        self.browser = browser
        self.extractor = extractor
        self.downloader = downloader
        self.config = config

    async def scrape_site(self) -> list[TopicData]:
        """Process all start URLs and return results."""
        results: list[TopicData] = []
        for url in self.config.start_urls:
            logger.info(f"Starting scrape: {url}")
            page_results = await self._scrape_start_url(url)
            results.extend(page_results)
        return results

    async def _scrape_start_url(self, start_url: str) -> list[TopicData]:
        """Handle pagination for a single start URL."""
        current_url: str | None = start_url
        all_topics: list[TopicData] = []
        
        while current_url:
            if not await self.browser.goto(current_url):
                logger.error(f"Failed to load: {current_url}")
                break

            content = await self.browser.get_content()
            self.extractor.set_content(content)
            
            # Extract topic links from current list page
            raw_links = self.extractor.select_attr(
                self.config.selectors["topic_preview"] + " " + self.config.selectors["topic_link"],
                "href",
                multiple=True
            )
            
            if isinstance(raw_links, list):
                for link in raw_links:
                    abs_link = urllib.parse.urljoin(current_url, link)
                    topic = await self._process_topic(abs_link)
                    if topic:
                        all_topics.append(topic)

            # Find next page
            next_page = self.extractor.select_attr(self.config.selectors["pagination_next"], "href")
            current_url = next_page if isinstance(next_page, str) else None
            
        return all_topics

    async def _process_topic(self, url: str) -> TopicData | None:
        """Navigate to a topic, extract fields, and download resources."""
        topic_id = TopicData.generate_id(url)
        logger.info(f"Processing topic: {topic_id} ({url})")
        
        if not await self.browser.goto(url):
            return None
            
        content = await self.browser.get_content()
        if len(content) < self.config.min_topic_content_length:
            return None
            
        self.extractor.set_content(content)
        topic_data = TopicData(topic_id=topic_id, topic_url=url)
        
        for field in self.config.fields_to_parse:
            if field.type == 'text':
                topic_data.fields[field.name] = self.extractor.select_text(field.selector, field.multiple)
            elif field.type == 'resource_url':
                res_url = self.extractor.select_attr(field.selector, field.attribute or "src")
                if isinstance(res_url, str):
                    path = await self.downloader.download(res_url, field.name, topic_data)
                    topic_data.fields[field.name] = path
                    
        return topic_data
