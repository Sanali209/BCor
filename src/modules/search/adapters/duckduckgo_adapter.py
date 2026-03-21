from typing import List
from duckduckgo_search import DDGS
from ..domain.interfaces import ISearchAdapter, SearchResult

class DuckDuckGoAdapter(ISearchAdapter):
    async def search_images(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Searches for images using DuckDuckGo."""
        results = []
        # DDGS is synchronous in most versions, but we wrap it in a thread pool if needed.
        # However, for the sake of simplicity in the adapter, we use it directly.
        with DDGS() as ddgs:
            ddgs_results = ddgs.images(query, max_results=limit)
            for r in ddgs_results:
                results.append(SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    image_url=r.get("image", ""),
                    thumbnail_url=r.get("thumbnail", ""),
                    source="DuckDuckGo"
                ))
        return results
