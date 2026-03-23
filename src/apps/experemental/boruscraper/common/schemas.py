import hashlib
import urllib.parse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from slugify import slugify

@dataclass
class FieldConfig:
    name: str
    selector: str
    type: str  # text, resource_url
    required: bool = False
    attribute: Optional[str] = None
    multiple: bool = False
    filter_regex: Optional[str] = None
    path_join_separator: Optional[str] = None
    exclude_extensions: Optional[List[str]] = field(default_factory=list)
    prepend_field_name: bool = False
    prepend_delimiter: str = "\\"
    is_tag: bool = False

@dataclass
class DelaysConfig:
    initial_manual_action_delay_s: int = 0
    delay_between_list_pages_s: float = 2.0
    delay_between_topics_s: float = 1.0
    download_delay_range_s: List[float] = field(default_factory=lambda: [0.5, 2.5])
    long_pause_every_n_pages: Dict[str, int] = field(default_factory=lambda: {"pages": 10, "seconds": 30})

@dataclass
class ScraperSettings:
    start_urls: List[Any] # Union[str, Dict[str, str]]
    save_path: str
    resource_save_path_pattern: str
    selectors: Dict[str, str]
    fields_to_parse: List[FieldConfig]
    delays: DelaysConfig
    min_topic_content_lent: int = 10000
    min_list_content_lent: int = 5000
    captcha_selector: Optional[str] = None
    navigation_timeout_ms: int = 60000
    download_timeout_ms: int = 45000
    scraping_direction: str = "forward"
    deduplication_threshold: int = 0
    exclude_extensions: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict) -> "ScraperSettings":
        fields = [FieldConfig(**f) for f in data.get("fields_to_parse", [])]
        delays_data = data.get("delays", {})
        delays = DelaysConfig(**delays_data) if isinstance(delays_data, dict) else DelaysConfig()
        
        known_keys = cls.__annotations__.keys()
        filtered_data = {k: v for k, v in data.items() if k in known_keys}
        filtered_data["fields_to_parse"] = fields
        filtered_data["delays"] = delays
        return cls(**filtered_data)

def extract_id_from_url(url: str) -> Optional[str]:
    try:
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        if "id" in query_params:
            return query_params["id"][0]
    except Exception:
        pass
    return None

@dataclass
class TopicData:
    topic_id: str
    topic_url: str
    fields: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def generate_id(url: str) -> str:
        extracted_id = extract_id_from_url(url)
        return extracted_id if extracted_id else hashlib.sha1(url.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
