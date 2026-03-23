import asyncio
import hashlib
import os
import random
import mimetypes
import urllib.parse
from typing import Optional, Dict, Any
from loguru import logger
from slugify import slugify
from playwright.async_api import BrowserContext, Page, Error as PlaywrightError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.apps.experemental.boruscraper.common.schemas import ScraperSettings, TopicData

class AsyncResourceDownloader:
    def __init__(self, settings: ScraperSettings, context: BrowserContext):
        self.settings = settings
        self.context = context
        self.page: Optional[Page] = None
        self.field_configs = {f.name: f for f in settings.fields_to_parse}

    def set_page(self, page: Optional[Page]):
        self.page = page

    def _get_extension(self, url: str, content_type: Optional[str]) -> str:
        if content_type:
            mime_type = content_type.split(";")[0].strip()
            ext = mimetypes.guess_extension(mime_type)
            if ext:
                return ext[1:] if ext.startswith(".") else ext
        path = urllib.parse.urlparse(url).path
        ext = os.path.splitext(path)[1]
        return ext[1:] if ext else "bin"

    def _format_path_component(self, value: Any, field_name: str) -> str:
        field_conf = self.field_configs.get(field_name)
        separator = field_conf.path_join_separator if field_conf else "_"
        if not separator: separator = "_"
        
        if isinstance(value, list):
            result = separator.join([slugify(str(item), separator=" ") for item in value if item])
            if len(result) > 240:
                result = result[:240]
            return result if result else "none"
            
        result = slugify(str(value)) if value is not None else ""
        if len(result) > 240:
             result = result[:240]
        return result if result else "none"

    async def download(self, resource_url: str, resource_field_name: str, topic_data: TopicData) -> Optional[Dict[str, Any]]:
        if not resource_url:
            return None

        url_ext = self._get_extension(resource_url, None)
        format_data = {
            "topic_id": slugify(str(topic_data.topic_id)),
            "field_name": slugify(resource_field_name),
            "ext": url_ext,
            **{fname: self._format_path_component(fvalue, fname) for fname, fvalue in topic_data.fields.items()}
        }
        
        delay_range = self.settings.delays.download_delay_range_s
        await asyncio.sleep(random.uniform(delay_range[0], delay_range[1]))

        body_bytes = None
        content_type = None

        try:
            @retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10),
                retry=retry_if_exception_type(PlaywrightError),
                reraise=True
            )
            async def _do_api_download():
                return await self.context.request.get(
                    resource_url, 
                    timeout=self.settings.download_timeout_ms,
                    headers={"Referer": topic_data.topic_url}
                )
            
            resp = await _do_api_download()
            if resp.ok:
                body_bytes = await resp.body()
                content_type = resp.headers.get("content-type")
        except PlaywrightError as e:
            logger.warning(f"API download failed after retries: {e}")

        if not body_bytes and self.page:
            try:
                @retry(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential(multiplier=1, min=2, max=10),
                    retry=retry_if_exception_type(PlaywrightError),
                    reraise=True
                )
                async def _do_nav_download():
                    return await self.page.goto(resource_url, wait_until="domcontentloaded", timeout=self.settings.download_timeout_ms)
                    
                resp = await _do_nav_download()
                if resp and resp.ok:
                    body_bytes = await resp.body()
                    content_type = resp.headers.get("content-type")
            except PlaywrightError as e:
                logger.warning(f"Nav download failed after retries: {e}")

        if not body_bytes:
            return None

        final_ext = self._get_extension(resource_url, content_type)
        if final_ext != url_ext:
            format_data["ext"] = final_ext
        
        relative_path = self.settings.resource_save_path_pattern.format(**format_data)
        abs_path = os.path.join(self.settings.save_path, relative_path)
        
        try:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "wb") as f:
                f.write(body_bytes)
            
            md5_hash = hashlib.md5(body_bytes).hexdigest()
            return {
                "relative_path": relative_path,
                "absolute_path": abs_path,
                "md5": md5_hash,
                "content_type": content_type
            }
        except IOError as e:
            logger.error(f"Save failed: {e}")
            return None
