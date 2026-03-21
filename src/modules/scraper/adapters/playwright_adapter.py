import asyncio
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from loguru import logger
import urllib.parse

from ..domain.interfaces import IScraperAdapter, ScraperConfig, ScraperResult, ScraperFieldConfig

class PlaywrightScraperAdapter(IScraperAdapter):
    async def scrape_page(self, config: ScraperConfig) -> ScraperResult:
        """Scrapes a page using Playwright and BeautifulSoup."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
                page = await context.new_page()
                
                logger.info(f"Navigating to {config.url}...")
                response = await page.goto(config.url, wait_until='domcontentloaded', timeout=config.timeout_ms)
                
                if not response or not response.ok:
                    return ScraperResult(
                        url=config.url,
                        fields={},
                        success=False,
                        error=f"Failed to load page: {response.status if response else 'No response'}"
                    )
                
                if config.wait_for_selector:
                    await page.wait_for_selector(config.wait_for_selector, timeout=config.timeout_ms)
                
                html_content = await page.content()
                await browser.close()
                
                # Parse with BeautifulSoup (more flexible for scraping)
                soup = BeautifulSoup(html_content, 'html.parser')
                results = {}
                
                for field in config.fields:
                    try:
                        results[field.name] = self._parse_field(soup, field, config.url)
                    except Exception as e:
                        if field.required:
                            raise e
                        logger.warning(f"Field {field.name} failed: {e}")
                        results[field.name] = None
                
                return ScraperResult(url=config.url, fields=results, success=True)
                
        except Exception as e:
            logger.exception(f"Scrape failed for {config.url}: {e}")
            return ScraperResult(url=config.url, fields={}, success=False, error=str(e))

    def _parse_field(self, soup: BeautifulSoup, field: ScraperFieldConfig, base_url: str) -> Any:
        elements = soup.select(field.selector)
        if not elements:
            if field.required:
                raise ValueError(f"Required field '{field.name}' not found")
            return None
            
        if field.type == 'text':
            if field.multiple:
                return [el.get_text(strip=True) for el in elements]
            return elements[0].get_text(strip=True)
            
        elif field.type == 'resource_url':
            attr = field.attribute or 'src'
            val = elements[0].get(attr)
            if val:
                return urllib.parse.urljoin(base_url, val)
            return None
            
        elif field.type == 'html':
            if field.multiple:
                return [str(el) for el in elements]
            return str(elements[0])
            
        return None
