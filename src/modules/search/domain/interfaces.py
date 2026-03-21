from typing import Protocol, List
from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    url: str
    image_url: str
    thumbnail_url: str = ""
    source: str = ""

class ISearchAdapter(Protocol):
    async def search_images(self, query: str, limit: int = 10) -> List[SearchResult]:
        ...
