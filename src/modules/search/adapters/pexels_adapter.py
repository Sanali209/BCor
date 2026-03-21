import httpx
from typing import List, Optional
from ..domain.interfaces import ISearchAdapter, SearchResult

class PexelsAdapter(ISearchAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pexels.com/v1/"
        self._headers = {"Authorization": self.api_key}

    async def search_images(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Searches for images using Pexels API."""
        params = {"query": query, "per_page": limit}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}search",
                headers=self._headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for photo in data.get("photos", []):
                results.append(SearchResult(
                    title=f"Photo by {photo.get('photographer', 'Unknown')}",
                    url=photo.get("url", ""),
                    image_url=photo.get("src", {}).get("original", ""),
                    thumbnail_url=photo.get("src", {}).get("medium", ""),
                    source="Pexels"
                ))
            return results
