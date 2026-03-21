"""Common web: configuration models.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FieldConfig:
    """Configuration for a single element extraction."""
    name: str
    selector: str
    type: str  # 'text' | 'resource_url'
    required: bool = False
    attribute: str | None = None
    multiple: bool = False
    filter_regex: str | None = None
    path_join_separator: str = "_"
    exclude_extensions: list[str] = field(default_factory=list)


@dataclass
class ScraperConfig:
    """Overall project configuration for a scraper."""
    start_urls: list[str]
    save_path: str
    selectors: dict[str, str]
    fields_to_parse: list[FieldConfig]
    resource_save_path_pattern: str = "resources/{field_name}/{topic_id}.{ext}"
    save_every_n_items: int = 10
    overwrite_metadata: bool = False
    overwrite_resources: bool = False
    min_topic_content_length: int = 5000
    navigation_timeout_ms: int = 60000
    download_timeout_ms: int = 30000
