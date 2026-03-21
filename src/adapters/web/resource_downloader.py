"""Web adapter: Resource downloader logic.
"""
from __future__ import annotations

import asyncio
import os
import random

import httpx
from loguru import logger

from src.common.web.topic import TopicData


class ResourceDownloader:
    """Async resource downloader with referrer support."""

    def __init__(self, save_path: str) -> None:
        self.save_path = save_path
        os.makedirs(save_path, exist_ok=True)

    async def download(
        self, 
        url: str, 
        field_name: str, 
        topic_data: TopicData,
        path_pattern: str = "resources/{field_name}/{topic_id}.{ext}"
    ) -> str | None:
        """Download a resource and return its relative path."""
        if not url:
            return None

        ext = url.split(".")[-1].split("?")[0] if "." in url else "bin"
        if len(ext) > 5:
            ext = "bin"  # Sanity check for long extensions

        rel_path = path_pattern.format(
            field_name=field_name,
            topic_id=topic_data.topic_id,
            ext=ext
        )
        abs_path = os.path.join(self.save_path, rel_path)

        if os.path.exists(abs_path):
            return rel_path

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        async with httpx.AsyncClient() as client:
            try:
                # Add delay to be polite
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                headers = {"Referer": topic_data.topic_url}
                response = await client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()
                
                with open(abs_path, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded: {rel_path}")
                return rel_path
            except Exception as e:
                logger.error(f"Failed to download {url}: {e}")
                return None
