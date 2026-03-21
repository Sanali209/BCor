"""Web adapter: Playwright implementation.
"""
from __future__ import annotations

from typing import Literal, Optional

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from src.core.web.i_browser import IBrowser


class PlaywrightAdapter(IBrowser):
    """Async Playwright browser adapter."""

    def __init__(self, headless: bool = True) -> None:
        self._headless = headless
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def _ensure_initialized(self) -> None:
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self._headless)
            self._context = await self._browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  # noqa: E501
                viewport={"width": 1920, "height": 1080},
            )
            self._page = await self._context.new_page()

    async def goto(self, url: str, wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] | None = "domcontentloaded") -> bool:
        await self._ensure_initialized()
        assert self._page is not None
        try:
            response = await self._page.goto(url, wait_until=wait_until)
            return response is not None and response.ok
        except Exception:
            return False

    async def get_content(self) -> str:
        await self._ensure_initialized()
        assert self._page is not None
        return await self._page.content()

    async def screenshot(self, path: str) -> None:
        await self._ensure_initialized()
        assert self._page is not None
        await self._page.screenshot(path=path)

    async def set_extra_headers(self, headers: dict[str, str]) -> None:
        await self._ensure_initialized()
        assert self._context is not None
        await self._context.set_extra_http_headers(headers)

    async def close(self) -> None:
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
