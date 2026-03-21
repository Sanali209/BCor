"""Core web: IExtractor port.

Abstracts HTML data extraction (BS4, lxml, etc.).
"""
from __future__ import annotations

import abc


class IExtractor(abc.ABC):
    """Port: HTML content extraction."""

    @abc.abstractmethod
    def set_content(self, html: str) -> None:
        """Load HTML content into the extractor."""
        raise NotImplementedError

    @abc.abstractmethod
    def select_text(self, selector: str, multiple: bool = False) -> str | None | list[str]:
        """Extract text content using a CSS selector."""
        raise NotImplementedError

    @abc.abstractmethod
    def select_attr(self, selector: str, attr: str, multiple: bool = False) -> str | None | list[str]:
        """Extract attribute value using a CSS selector."""
        raise NotImplementedError
