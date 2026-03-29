from dataclasses import dataclass, field
from typing import Any, Optional
from src.modules.agm.mapper import AGMMapper
from src.modules.assets.domain.models import Asset, ContentChunk


@dataclass
class SearchQuery:
    """Parameters for an asset search operation."""
    text: str
    mime_filter: str | None = None
    tag_ids: list[str] = field(default_factory=list)
    chunk_mode: str = "parent"
    limit: int = 20
    skip: int = 0


@dataclass
class SearchResult:
    """A single search result."""
    item: Asset
    score: float
    chunk: Optional[ContentChunk] = None


class SearchService:
    """High-level search abstraction over Neo4j via CypherQuery DSL."""

    def __init__(self, mapper: AGMMapper) -> None:
        self._mapper = mapper

    async def search(self, query: SearchQuery, session: Any) -> list[SearchResult]:
        """Execute a search query and return ranked results.
        
        This implementation uses the Fluent Cypher DSL for most filters,
        and raw full-text if needed (though CypherQuery will be extended).
        """
        # Start a fluent query on the Asset base class
        q = self._mapper.query(Asset, session=session)
        
        # Apply filters declaratively
        if query.text:
            # Simple full-text filter (simulated via Lucene-style search in where)
            q = q.where(f"n.name CONTAINS '{query.text}' OR n.description CONTAINS '{query.text}'")
            
        if query.mime_filter:
            # Handle glob patterns (e.g., image/* -> STARTS WITH image/)
            if query.mime_filter.endswith("*"):
                prefix = query.mime_filter[:-1]
                q = q.where(f"n.mime_type STARTS WITH '{prefix}'")
            else:
                q = q.where(f"n.mime_type = '{query.mime_filter}'")
                
        if query.tag_ids:
            # Tag filtering via relationship (Fluent API doesn't support complex joins yet, 
            # but we can use where logic for now or raw match if needed)
            # For now, we'll use a simplified where IN clause assuming tag names/ids are on n
            q = q.where(f"ANY(tag IN [(n)-[:HAS_TAG]->(t) | t.id] WHERE tag IN {query.tag_ids})")

        # Apply ordering and pagination
        q = q.limit(query.limit).skip(query.skip)
        
        # Execute and map to SearchResult
        assets = await q.fetch()
        return [SearchResult(item=asset, score=1.0) for asset in assets]
