"""Common web: topic data model.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TopicData:
    """Represents a single scraped item."""
    topic_id: str
    topic_url: str
    fields: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def generate_id(url: str) -> str:
        """Deterministic ID from URL."""
        return hashlib.sha1(url.encode("utf-8")).hexdigest()
