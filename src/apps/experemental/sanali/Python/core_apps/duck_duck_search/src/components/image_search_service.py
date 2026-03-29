"""
Image Search Service Component for DuckDuckGo integration.

Provides DuckDuckGo image search functionality with SLM framework integration,
progress tracking, and async operation support.
"""

import asyncio
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from loguru import logger

from SLM.core.component import Component
from .progress_service import ProgressService


@dataclass
class SearchResult:
    """Represents a single image search result."""

    title: str
    url: str
    image_url: str
    thumbnail_url: str
    source: str
    description: str = ""
    width: int = 0
    height: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "image_url": self.image_url,
            "thumbnail_url": self.thumbnail_url,
            "source": self.source,
            "description": self.description,
            "width": self.width,
            "height": self.height
        }


class ImageSearchService(Component):
    """
    DuckDuckGo image search service with SLM integration.

    Features:
    - Async DuckDuckGo search API integration
    - Progress tracking for search operations
    - Search result caching and management
    - Configurable search parameters
    - Integration with SLM progress service
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name or "image_search_service")

        # Search configuration
        self.max_results = 200
        self.region = "wt-wt"
        self.safe_search = "moderate"
        self.default_timeout = 10

        # Search history and caching
        self.search_history: List[Dict[str, Any]] = []
        self.result_cache: Dict[str, List[SearchResult]] = {}
        self.max_history_size = 50

    async def on_initialize_async(self):
        """Initialize the image search service."""
        # Load settings from settings service if available
        await self._load_settings()
        logger.info("Image search service initialized")

    async def on_start_async(self):
        """Start the image search service."""
        logger.info("Image search service started")

    async def on_shutdown_async(self):
        """Shutdown the image search service."""
        self.search_history.clear()
        self.result_cache.clear()
        logger.info("Image search service shutdown")

    async def search_images(
        self,
        query: str,
        max_results: Optional[int] = None,
        region: Optional[str] = None,
        safe_search: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search for images using DuckDuckGo.

        Args:
            query: Search query string
            max_results: Maximum number of results (uses setting if None)
            region: Search region (uses setting if None)
            safe_search: Safe search level (uses setting if None)

        Returns:
            List of search results
        """
        if not query.strip():
            logger.warning("Empty search query provided")
            return []

        # Use provided parameters or fall back to settings
        search_max_results = max_results or self.max_results
        search_region = region or self.region
        search_safe_search = safe_search or self.safe_search

        # Check cache first
        cache_key = self._make_cache_key(query, search_max_results, search_region, search_safe_search)
        if cache_key in self.result_cache:
            logger.debug(f"Returning cached results for query: {query}")
            return self.result_cache[cache_key]

        # Start progress tracking
        progress_service = await self._get_progress_service()
        operation_id = None

        if progress_service:
            operation_id = await progress_service.start_operation(
                f"search_images_{query[:30]}",
                total_steps=search_max_results,
                metadata={
                    "query": query,
                    "max_results": search_max_results,
                    "region": search_region
                }
            )

        try:
            # Perform the search
            results = await self._perform_search(
                query,
                search_max_results,
                search_region,
                search_safe_search,
                operation_id,
                progress_service
            )

            # Cache the results
            self.result_cache[cache_key] = results

            # Add to search history
            await self._add_to_history(query, len(results))

            # Complete progress tracking
            if operation_id and progress_service:
                await progress_service.complete_operation(operation_id)

            logger.info(f"Search completed: {query} -> {len(results)} results")
            return results

        except Exception as e:
            # Fail progress tracking
            if operation_id and progress_service:
                await progress_service.fail_operation(operation_id, e)

            logger.error(f"Search failed for query '{query}': {e}")
            raise

    async def _perform_search(
        self,
        query: str,
        max_results: int,
        region: str,
        safe_search: str,
        operation_id: Optional[str],
        progress_service: Optional[Any]
    ) -> List[SearchResult]:
        """
        Perform the actual DuckDuckGo search.

        Args:
            query: Search query
            max_results: Maximum results to fetch
            region: Search region
            safe_search: Safe search setting
            operation_id: Progress operation ID
            progress_service: Progress service instance

        Returns:
            List of search results
        """
        try:
            from duckduckgo_search import DDGS

            results = []
            with DDGS() as ddgs:
                # Perform async search
                search_results = list(ddgs.images(
                    keywords=query,
                    region=region,
                    safesearch=safe_search,
                    max_results=max_results
                ))

                # Process results
                for i, result in enumerate(search_results):
                    try:
                        # Handle width and height conversion
                        width = result.get('width', 0)
                        height = result.get('height', 0)
                        if isinstance(width, str):
                            try:
                                width = int(width)
                            except ValueError:
                                width = 0
                        if isinstance(height, str):
                            try:
                                height = int(height)
                            except ValueError:
                                height = 0

                        search_result = SearchResult(
                            title=result.get('title', 'No title'),
                            url=result.get('url', ''),
                            image_url=result.get('image', ''),
                            thumbnail_url=result.get('thumbnail', ''),
                            source=result.get('source', 'Unknown'),
                            description=result.get('description', ''),
                            width=width,
                            height=height
                        )

                        results.append(search_result)

                        # Update progress
                        if operation_id and progress_service:
                            await progress_service.update_progress(
                                operation_id,
                                i + 1,
                                metadata={"current_result": i + 1, "total": max_results}
                            )

                    except Exception as e:
                        logger.warning(f"Error processing search result {i}: {e}")
                        continue

            return results

        except ImportError:
            logger.error("duckduckgo-search library not installed")
            raise RuntimeError("Search library not available")
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            raise

    def get_search_history(self) -> List[Dict[str, Any]]:
        """
        Get search history.

        Returns:
            List of recent searches with metadata
        """
        return self.search_history.copy()

    def clear_search_history(self):
        """Clear search history."""
        self.search_history.clear()
        logger.info("Search history cleared")

    def clear_result_cache(self):
        """Clear result cache."""
        self.result_cache.clear()
        logger.info("Result cache cleared")

    def get_cached_results(self, query: str) -> Optional[List[SearchResult]]:
        """
        Get cached results for a query.

        Args:
            query: Search query to look up

        Returns:
            Cached results or None if not found
        """
        # Try different cache keys with current settings
        cache_keys = [
            self._make_cache_key(query, self.max_results, self.region, self.safe_search),
            self._make_cache_key(query, 50, self.region, self.safe_search),
            self._make_cache_key(query, 100, self.region, self.safe_search),
        ]

        for key in cache_keys:
            if key in self.result_cache:
                return self.result_cache[key]

        return None

    def _make_cache_key(self, query: str, max_results: int, region: str, safe_search: str) -> str:
        """
        Generate a cache key for search parameters.

        Args:
            query: Search query
            max_results: Maximum results
            region: Search region
            safe_search: Safe search setting

        Returns:
            Cache key string
        """
        # Sanitize query for cache key
        sanitized_query = re.sub(r'\s+', '_', query.strip().lower())[:50]
        return f"{sanitized_query}_{max_results}_{region}_{safe_search}"

    async def _load_settings(self):
        """Load settings from settings service."""
        try:
            if self.message_bus:
                # Try to get settings from message bus
                await self.message_bus.publish_async(
                    "settings.get",
                    key="app.search"
                )

                # For now, use default settings - settings service integration
                # will be handled by the main application

        except Exception as e:
            logger.warning(f"Could not load settings: {e}")

    async def _add_to_history(self, query: str, result_count: int):
        """Add search to history."""
        import time

        history_entry = {
            "query": query,
            "result_count": result_count,
            "timestamp": time.time(),
            "max_results": self.max_results,
            "region": self.region
        }

        self.search_history.append(history_entry)

        # Trim history if too large
        if len(self.search_history) > self.max_history_size:
            self.search_history = self.search_history[-self.max_history_size:]

    async def _get_progress_service(self) -> Optional[Any]:
        """Get progress service instance."""
        try:
            # For now, return None - progress service integration
            # will be handled by the main application through message bus events
            return None
        except:
            pass
        return None

    def get_popular_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most popular search queries from history.

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of popular queries with counts
        """
        from collections import Counter

        query_counts = Counter(entry["query"] for entry in self.search_history)

        popular = [
            {"query": query, "count": count}
            for query, count in query_counts.most_common(limit)
        ]

        return popular

    def get_search_stats(self) -> Dict[str, Any]:
        """
        Get search service statistics.

        Returns:
            Dictionary with search statistics
        """
        return {
            "total_searches": len(self.search_history),
            "cached_queries": len(self.result_cache),
            "cache_size_mb": len(str(self.result_cache)) / (1024 * 1024),  # Rough estimate
            "max_results": self.max_results,
            "region": self.region,
            "safe_search": self.safe_search
        }
