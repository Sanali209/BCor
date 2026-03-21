"""Web adapter: BeautifulSoup extractor implementation.
"""
from __future__ import annotations

from typing import Any, List, Optional

from bs4 import BeautifulSoup

from src.core.web.i_extractor import IExtractor


class BS4Extractor(IExtractor):
    """BeautifulSoup-based HTML extractor."""

    def __init__(self) -> None:
        self._soup: BeautifulSoup | None = None

    def set_content(self, html: str) -> None:
        self._soup = BeautifulSoup(html, "lxml")

    def select_text(self, selector: str, multiple: bool = False) -> str | None | list[str]:
        if not self._soup:
            return [] if multiple else None
        
        elements = self._soup.select(selector)
        if not elements:
            return [] if multiple else None

        texts = [el.get_text(strip=True) for el in elements]
        return texts if multiple else texts[0]

    def select_attr(self, selector: str, attr: str, multiple: bool = False) -> str | None | list[str]:
        if not self._soup:
            return [] if multiple else None

        elements = self._soup.select(selector)
        if not elements:
            return [] if multiple else None

        values = [el.get(attr) for el in elements if el.get(attr)]
        return values if multiple else (values[0] if values else None)  # type: ignore
