"""Core web: IBrowser port.

Abstracts browser automation (Playwright, Selenium, etc.).
"""
from __future__ import annotations

import abc
from typing import Literal


class IBrowser(abc.ABC):
    """Port: browser automation functionality."""

    @abc.abstractmethod
    async def goto(self, url: str, wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] | None = "domcontentloaded") -> bool:
        """Navigate to a URL."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_content(self) -> str:
        """Return the current page HTML content."""
        raise NotImplementedError

    @abc.abstractmethod
    async def screenshot(self, path: str) -> None:
        """Capture a screenshot to the given path."""
        raise NotImplementedError

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the browser and cleanup."""
        raise NotImplementedError

    @abc.abstractmethod
    async def set_extra_headers(self, headers: dict[str, str]) -> None:
        """Set extra HTTP headers (e.g., Referer)."""
        raise NotImplementedError
