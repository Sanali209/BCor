import asyncio
import time
import urllib.parse
import os
import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from loguru import logger
from dataclasses import asdict
from playwright.async_api import async_playwright, Page, Error as PlaywrightError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.core.messagebus import MessageBus
from src.core.unit_of_work import AbstractUnitOfWork
from src.apps.experemental.boruscraper.common.database import DatabaseManager
from src.apps.experemental.boruscraper.common.deduplication import DeduplicationManager
from src.apps.experemental.boruscraper.common.schemas import ScraperSettings, TopicData
from src.apps.experemental.boruscraper.common.metadata import MetadataWriter
from src.apps.experemental.boruscraper.common.downloader import AsyncResourceDownloader
from src.apps.experemental.boruscraper.application.messages import (
    ScrapeLogEvent, ScrapeStatsEvent, DuplicateFoundEvent, 
    CaptchaDetectedEvent, DebugConfirmationEvent, MinContentWarningEvent,
    WorkerFinishedEvent
)

from src.porting.async_utils import TaskThrottler

class ScrapeProjectUseCase:
    """Use case to scrape an entire project using async Playwright."""
    
    def __init__(self, bus: MessageBus, uow: AbstractUnitOfWork, db: DatabaseManager, dedup: DeduplicationManager):
        self.bus = bus
        self.uow = uow
        self.db = db
        self.dedup = dedup
        
        self.is_running = True
        self.is_paused = False
        self.is_waiting_for_debug = False
        self.debug_mode = False
        self.resolution_action: Optional[str] = None
        self.metadata_writer = MetadataWriter()
        self.throttler = TaskThrottler(concurrency_limit=5) # Default limit

    async def _emit_log(self, project_id: int, msg: str, level: str = "INFO"):
        logger.log(level.upper(), msg)
        await self.bus.dispatch(ScrapeLogEvent(project_id=project_id, message=msg))

    async def _wait_if_paused(self):
        while self.is_paused and self.is_running:
            await asyncio.sleep(0.5)

    async def _wait_for_confirmation(self, project_id: int, message: str):
        if not self.debug_mode:
            return
        
        self.is_waiting_for_debug = True
        await self.bus.dispatch(DebugConfirmationEvent(project_id=project_id, message=message))
        while self.is_waiting_for_debug and self.is_running:
            await asyncio.sleep(0.5)

    def confirm_step(self):
        self.is_waiting_for_debug = False

    async def execute(self, project_id: int, debug_mode: bool = False):
        self.debug_mode = debug_mode
        settings_dict = self.db.get_project_settings(project_id)
        if not settings_dict:
            await self._emit_log(project_id, "No valid config found", "ERROR")
            await self.bus.dispatch(WorkerFinishedEvent(project_id=project_id, status="Error"))
            return

        settings = ScraperSettings.from_dict(settings_dict)
        project_name = self.db.get_project_name(project_id)
        
        logger.info(f"ScrapeProjectUseCase: Initialized with project '{project_name}' (ID: {project_id})")
        logger.info(f"ScrapeProjectUseCase: Start URLs: {settings.start_urls}")

        session_stats = {"pages": 0, "topics": 0, "images": 0, "images_failed": 0, "start_time": time.time()}

        async def _emit_stats():
            elapsed = time.time() - session_stats["start_time"]
            pages_min = (session_stats["pages"] / elapsed) * 60 if elapsed > 0 else 0
            images_min = (session_stats["images"] / elapsed) * 60 if elapsed > 0 else 0
            stats_out = dict(session_stats)
            stats_out["pages_per_min"] = pages_min
            stats_out["images_per_min"] = images_min
            await self.bus.dispatch(ScrapeStatsEvent(project_id=project_id, stats=stats_out))

        await self._emit_log(project_id, f"Starting scrape for {project_id}")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context(viewport={"width": 1920, "height": 1080})
                page = await context.new_page()
                
                downloader = AsyncResourceDownloader(settings, context)
                downloader.set_page(page)

                for start_entry in list(settings.start_urls):
                    if not self.is_running: break

                    start_url = start_entry
                    if isinstance(start_entry, dict):
                        direction = settings.scraping_direction
                        start_url = start_entry.get(direction, "")
                        if not start_url:
                            continue

                    state = self.db.get_pagination_state(project_id, start_url)
                    current_url = state['last_page_url'] if state else start_url
                    
                    await self._emit_log(project_id, f"Processing Start URL: {start_url} (Resuming {current_url})")

                    while current_url and self.is_running:
                        await self._wait_if_paused()
                        
                        try:
                            @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(PlaywrightError), reraise=True)
                            async def _do_nav():
                                return await page.goto(current_url, wait_until="domcontentloaded", timeout=settings.navigation_timeout_ms)
                                
                            resp = await _do_nav()
                            if not resp or not resp.ok:
                                await self._emit_log(project_id, f"Failed to load {current_url}", "WARNING")
                                if settings.captcha_selector and await page.query_selector(settings.captcha_selector):
                                    await self.bus.dispatch(CaptchaDetectedEvent(project_id=project_id, url=current_url))
                                    self.is_paused = True
                                    continue
                                await asyncio.sleep(5)
                                continue
                        except Exception as e:
                            await self._emit_log(project_id, f"Nav error: {e}", "ERROR")
                            break

                        content = await page.content()
                        soup = BeautifulSoup(content, "lxml")

                        topic_previews = soup.select(settings.selectors["topic_preview"])
                        topic_links = []
                        for preview in topic_previews:
                            link_el = preview.select_one(settings.selectors["topic_link"])
                            if link_el and link_el.get("href"):
                                topic_links.append(urllib.parse.urljoin(current_url, link_el["href"]))

                        for topic_url in topic_links:
                            if not self.is_running: break
                            await self._wait_if_paused()
                            
                            await self._wait_for_confirmation(project_id, f"Processing topic: {topic_url}")
                            processed = await self._process_topic(project_id, project_name, page, downloader, settings, topic_url, session_stats)
                            wait_time = settings.delays.delay_between_topics_s if processed else 0.01
                            await asyncio.sleep(wait_time)
                            
                            if processed:
                                session_stats["topics"] += 1
                                await _emit_stats()

                        if not self.is_running: break

                        selector_key = "pagination_prev" if settings.scraping_direction == "backward" else "pagination_next"
                        next_selector = settings.selectors.get(selector_key)
                        next_el = soup.select_one(next_selector) if next_selector else None
                        
                        if next_el and next_el.get("href"):
                            next_url = urllib.parse.urljoin(current_url, next_el["href"])
                            self.db.update_pagination_state(project_id, start_url, next_url, direction=settings.scraping_direction)
                            current_url = next_url
                            session_stats["pages"] += 1
                            await _emit_stats()
                            await asyncio.sleep(settings.delays.delay_between_list_pages_s)
                        else:
                            current_url = None
                            self.db.delete_pagination_state(project_id, start_url)
                            if start_entry in settings.start_urls:
                                settings.start_urls.remove(start_entry)
                                settings.start_urls.append(start_entry)
                                import json
                                self.db.update_project_settings(project_id, json.dumps(asdict(settings)))

                if self.is_running:
                    self.db.move_project_to_end_of_queue(project_id)

        except Exception as e:
            await self._emit_log(project_id, f"Critical Error: {str(e)}", "ERROR")
        finally:
            await self.bus.dispatch(WorkerFinishedEvent(project_id=project_id, status="Finished"))

    async def _process_topic(self, project_id, project_name, page, downloader, settings, topic_url, stats: dict) -> bool:
        async with self.throttler:
            topic_id = TopicData.generate_id(topic_url)
            
            async with self.uow:
                # check exists using UnitOfWork instead of db directly if possible, or direct db
                if self.db.post_exists(project_id, topic_id): 
                    return False
    
                try:
                    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(PlaywrightError), reraise=True)
                    async def _do_topic_nav():
                        await page.goto(topic_url, wait_until="domcontentloaded", timeout=settings.download_timeout_ms)
                    await _do_topic_nav()
                except Exception as e:
                    return False
    
                content = await page.content()
                soup = BeautifulSoup(content, "lxml")
                topic_data = TopicData(topic_id, topic_url)
    
                for field_conf in settings.fields_to_parse:
                    elements = soup.select(field_conf.selector)
                    
                    if field_conf.type == "text":
                        texts = [el.get_text(strip=True) for el in elements]
                        if field_conf.filter_regex:
                            regex = re.compile(field_conf.filter_regex)
                            texts = [t for t in texts if not regex.search(t)]
                        if field_conf.prepend_field_name:
                            texts = [f"{field_conf.name}{field_conf.prepend_delimiter}{t}" for t in texts]
    
                        topic_data.fields[field_conf.name] = texts if field_conf.multiple else (texts[0] if texts else None)
                    
                    elif field_conf.type == "resource_url":
                        urls = []
                        attr = field_conf.attribute or "src"
                        for el in elements:
                            if url := el.get(attr):
                                urls.append(urllib.parse.urljoin(topic_url, url))
                        
                        if urls:
                            target_urls = urls if field_conf.multiple else urls[:1]
                            downloaded_info = []
                            for i, res_url in enumerate(target_urls):
                                _, ext = os.path.splitext(urllib.parse.urlparse(res_url).path)
                                if ext and ext.lstrip('.').lower() in [e.lower() for e in settings.exclude_extensions]:
                                    continue
    
                                fname = f"{field_conf.name}_{i}" if len(target_urls) > 1 else field_conf.name
                                result = await downloader.download(res_url, fname, topic_data)
                                
                                if result:
                                    stats["images"] += 1
                                    dhash = self.dedup.calculate_dhash(result['absolute_path'])
                                    is_dupe, conflicts, _ = self.dedup.check_is_duplicate(dhash, project_id, settings.deduplication_threshold)
                                    
                                    if is_dupe:
                                        await self.bus.dispatch(DuplicateFoundEvent(project_id=project_id, data={"path": result['absolute_path'], "conflicts": [dict(c) for c in conflicts]}))
                                        self.is_paused = True
                                        while self.is_paused and self.is_running:
                                            await asyncio.sleep(0.5)
                                        
                                        if self.resolution_action == 'SKIP':
                                            if os.path.exists(result['absolute_path']): os.remove(result['absolute_path'])
                                            self.resolution_action = None
                                            continue
                                        elif self.resolution_action == 'REPLACE':
                                            for conf in conflicts:
                                                old_abs = os.path.join(conf.get('save_path', ''), conf.get('relative_path') or conf.get('file_path', ''))
                                                if os.path.exists(old_abs): os.remove(old_abs)
                                            self.resolution_action = None
    
                                    if not hasattr(topic_data, '_pending_resources'):
                                        topic_data._pending_resources = []
                                    topic_data._pending_resources.append({
                                        'relative_path': result['relative_path'],
                                        'dhash': dhash,
                                        'md5': result['md5']
                                    })
                                    
                                    downloaded_info.append(result['relative_path'])
                                else:
                                    stats["images_failed"] += 1
                            
                            topic_data.fields[field_conf.name] = downloaded_info if field_conf.multiple else (downloaded_info[0] if downloaded_info else None)
                
                if not self.is_running: return False
    
                post_id = self.db.save_post(project_id, topic_id, topic_data.to_dict())
                if hasattr(topic_data, '_pending_resources'):
                    for res in topic_data._pending_resources:
                        self.db.save_resource(post_id, res['relative_path'], res['dhash'], res['md5'])
                        
                self.uow.commit()
    
            return True

