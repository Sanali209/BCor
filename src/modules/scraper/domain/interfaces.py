from typing import Protocol, List, Dict, Any, Optional
from pydantic import BaseModel

class ScraperFieldConfig(BaseModel):
    name: str
    selector: str
    type: str  # 'text', 'resource_url', 'html'
    required: bool = False
    attribute: Optional[str] = None
    multiple: bool = False

class ScraperConfig(BaseModel):
    url: str
    fields: List[ScraperFieldConfig]
    wait_for_selector: Optional[str] = None
    timeout_ms: int = 30000

class ScraperResult(BaseModel):
    url: str
    fields: Dict[str, Any]
    success: bool
    error: Optional[str] = None

class IScraperAdapter(Protocol):
    async def scrape_page(self, config: ScraperConfig) -> ScraperResult:
        ...
