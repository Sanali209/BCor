from typing import Any, Generic, Optional, Type, TypeVar, Union, TYPE_CHECKING, List, Dict, Tuple
import asyncio

if TYPE_CHECKING:
    from src.modules.agm.mapper import AGMMapper

T = TypeVar("T")

class CypherQuery(Generic[T]):
    """Fluent query builder for BCor AGM models.
    
    Allows chaining filters, matches, and pagination before executing
    the query through the AGMMapper and returning domain objects.
    Now supports CONTAINS, RANGE, and Vector NEAR search.
    """
    
    def __init__(self, mapper: "AGMMapper", model_class: Type[T]):
        self._mapper = mapper
        self._model_class = model_class
        self._filters: Dict[str, Any] = {}
        self._contains_filters: Dict[str, str] = {}
        self._range_filters: Dict[str, Tuple[Any, Any]] = {}
        self._vector_info: Optional[Dict[str, Any]] = None
        
        self._limit: Optional[int] = None
        self._skip: Optional[int] = None
        self._order_by: Optional[str] = None
        self._matches: List[str] = []
        
    def where(self, **kwargs) -> "CypherQuery[T]":
        """Adds property-based equality filters to the query."""
        self._filters.update(kwargs)
        return self
        
    def contains(self, field: str, value: str) -> "CypherQuery[T]":
        """Adds a case-sensitive substring filter (CONTAINS)."""
        self._contains_filters[field] = value
        return self
        
    def range(self, field: str, start: Any, end: Any) -> "CypherQuery[T]":
        """Adds a range filter for numeric or date fields."""
        self._range_filters[field] = (start, end)
        return self
        
    def near(self, field: str, vector: List[float], limit: int = 10) -> "CypherQuery[T]":
        """Adds a vector similarity filter (Semantic Search).
        
        Args:
            field: Name of the vector-indexed field.
            vector: The query vector.
            limit: How many neighbors to retrieve within the vector query.
        """
        self._vector_info = {
            "field": field,
            "vector": vector,
            "limit": limit
        }
        return self

    def limit(self, value: int) -> "CypherQuery[T]":
        """Sets the maximum number of results to return."""
        self._limit = value
        return self
        
    def skip(self, value: int) -> "CypherQuery[T]":
        """Sets the number of initial results to skip."""
        self._skip = value
        return self
        
    def order_by(self, field: str) -> "CypherQuery[T]":
        """Sets the field name to order the results by."""
        self._order_by = field
        return self

    def build_cypher(self) -> Tuple[str, Dict[str, Any]]:
        """Generates the Cypher statement and parameters."""
        label = getattr(self._model_class, "__label__", self._model_class.__name__)
        params = {}
        clauses = []

        # 1. Start with Vector Search CALL or base MATCH
        if self._vector_info:
            vec_field = self._vector_info["field"]
            # Convention: vec_{Label}_{Field}
            index_name = f"vec_{label}_{vec_field}"
            params["p_vector"] = self._vector_info["vector"]
            params["p_limit"] = self._vector_info["limit"]
            clauses.append(f"CALL db.index.vector.queryNodes('{index_name}', $p_limit, $p_vector) YIELD node AS n, score")
        else:
            clauses.append(f"MATCH (n:{label})")
        
        # 2. Add WHERE filters
        where_parts = []
        
        # Equality filters
        for key, value in self._filters.items():
            param_name = f"p_{key}"
            where_parts.append(f"n.{key} = ${param_name}")
            params[param_name] = value
            
        # CONTAINS filters
        for key, value in self._contains_filters.items():
            param_name = f"p_{key}_contains"
            where_parts.append(f"n.{key} CONTAINS ${param_name}")
            params[param_name] = value
            
        # RANGE filters
        for key, (start, end) in self._range_filters.items():
            start_param = f"p_{key}_start"
            end_param = f"p_{key}_end"
            where_parts.append(f"n.{key} >= ${start_param} AND n.{key} <= ${end_param}")
            params[start_param] = start
            params[end_param] = end
            
        if where_parts:
            clauses.append("WHERE " + " AND ".join(where_parts))
            
        # 3. RETURN clause
        return_stmt = "RETURN n, labels(n) as labels, elementId(n) as id"
        if self._vector_info:
            return_stmt += ", score"
        clauses.append(return_stmt)
        
        # 4. Global ORDER BY
        if self._order_by:
            clauses.append(f"ORDER BY n.{self._order_by}")
        elif self._vector_info:
            # If vector search, allow Neo4j's default descending score ordering
            pass
            
        # 5. Global LIMIT / SKIP
        if self._skip is not None:
            clauses.append(f"SKIP {self._skip}")
        if self._limit is not None:
            clauses.append(f"LIMIT {self._limit}")
            
        return " ".join(clauses), params

    async def all(self, session: Any) -> List[T]:
        """Executes the query and returns matching domain objects."""
        query_str, params = self.build_cypher()
        result = await session.run(query_str, **params)
        records = await result.data()
        
        instances = []
        for record in records:
            node = record["n"]
            node_data = dict(node)
            node_data["id"] = record["id"]
            node_data["labels"] = record["labels"]
            
            # Map score if present (for viewmodels to display)
            if "score" in record:
                node_data["_score"] = record["score"]
            
            instance = await self._mapper.load(self._model_class, node_data)
            instances.append(instance)
            
        return instances

    async def first(self, session: Any) -> Optional[T]:
        """Executes the query and returns the first result or None."""
        self.limit(1)
        results = await self.all(session)
        return results[0] if results else None

    async def delete(self, session: Any) -> int:
        """Deletes all nodes matching the query criteria."""
        label = getattr(self._model_class, "__label__", self._model_class.__name__)
        # Delete doesn't support vector search context easily, 
        # normally delete is for filtered cleanup.
        clauses = [f"MATCH (n:{label})"]
        query_str, params = self.build_cypher()
        
        # Extract WHERE parts from build_cypher if needed, 
        # or simplified re-implementation for delete.
        # For PoC, let's just use MATCH + WHERE + DETACH DELETE
        
        # Actually, let's just rebuild a simplified version for delete
        temp_query = " ".join([c for c in query_str.split(" ") if "RETURN" not in c and "ORDER BY" not in c and "LIMIT" not in c and "SKIP" not in c])
        query_str = f"{temp_query} DETACH DELETE n"
        
        result = await session.run(query_str, **params)
        summary = await result.consume()
        return summary.counters.nodes_deleted
