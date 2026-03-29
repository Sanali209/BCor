from typing import Any, Generic, Optional, Type, TypeVar, Union, TYPE_CHECKING
import asyncio

if TYPE_CHECKING:
    from src.modules.agm.mapper import AGMMapper

T = TypeVar("T")

class CypherQuery(Generic[T]):
    """Fluent query builder for BCor AGM models.
    
    Allows chaining filters, matches, and pagination before executing
    the query through the AGMMapper and returning domain objects.
    """
    
    def __init__(self, mapper: "AGMMapper", model_class: Type[T]):
        self._mapper = mapper
        self._model_class = model_class
        self._filters: dict[str, Any] = {}
        self._limit: Optional[int] = None
        self._skip: Optional[int] = None
        self._order_by: Optional[str] = None
        self._matches: list[str] = []
        self._return_fields: list[str] = ["n"]
        
    def where(self, **kwargs) -> "CypherQuery[T]":
        """Adds property-based filters to the query.
        
        Args:
            **kwargs: Property names and values to filter by.
        """
        self._filters.update(kwargs)
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

    def build_cypher(self) -> tuple[str, dict[str, Any]]:
        """Generates the Cypher statement and parameters.
        
        Returns:
            A tuple of (cypher_string, parameters_dict).
        """
        label = getattr(self._model_class, "__label__", self._model_class.__name__)
        
        # Base MATCH
        clauses = [f"MATCH (n:{label})"]
        
        # WHERE
        params = {}
        if self._filters:
            where_parts = []
            for key, value in self._filters.items():
                param_name = f"p_{key}"
                where_parts.append(f"n.{key} = ${param_name}")
                params[param_name] = value
            clauses.append("WHERE " + " AND ".join(where_parts))
            
        # RETURN
        clauses.append("RETURN n, labels(n) as labels, elementId(n) as id")
        
        # ORDER BY
        if self._order_by:
            clauses.append(f"ORDER BY n.{self._order_by}")
            
        # LIMIT / SKIP
        if self._skip is not None:
            clauses.append(f"SKIP {self._skip}")
        if self._limit is not None:
            clauses.append(f"LIMIT {self._limit}")
            
        return " ".join(clauses), params

    async def all(self, session: Any) -> list[T]:
        """Executes the query and returns all matching domain objects.
        
        Args:
            session: The Neo4j async session to use for execution.
        """
        query_str, params = self.build_cypher()
        result = await session.run(query_str, **params)
        records = await result.data()
        
        instances = []
        for record in records:
            # Reconstruct the expected 'record' format for AGMMapper.load
            # which expects properties + id + labels
            node = record["n"]
            node_data = dict(node)
            node_data["id"] = record["id"]
            node_data["labels"] = record["labels"]
            
            instance = await self._mapper.load(self._model_class, node_data)
            instances.append(instance)
            
        return instances

    async def first(self, session: Any) -> Optional[T]:
        """Executes the query and returns the first result or None."""
        self.limit(1)
        results = await self.all(session)
        return results[0] if results else None

    async def delete(self, session: Any) -> int:
        """Deletes all nodes matching the query criteria.
        
        Args:
            session: The Neo4j async session.

        Returns:
            The number of nodes deleted.
        """
        label = getattr(self._model_class, "__label__", self._model_class.__name__)
        clauses = [f"MATCH (n:{label})"]
        
        params = {}
        if self._filters:
            where_parts = []
            for key, value in self._filters.items():
                param_name = f"p_{key}"
                where_parts.append(f"n.{key} = ${param_name}")
                params[param_name] = value
            clauses.append("WHERE " + " AND ".join(where_parts))
            
        clauses.append("DETACH DELETE n")
        query_str = " ".join(clauses)
        
        result = await session.run(query_str, **params)
        summary = await result.consume()
        return summary.counters.nodes_deleted
