from typing import (
    Annotated,
    Any,
    Generic,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)

from loguru import logger

from src.modules.agm.mapper import AGMMapper
from src.modules.agm.metadata import Live, Rel

T = TypeVar("T")


class QueryBuilder(Generic[T]):
    """Fluent API for querying the graph and loading domain models.

    QueryBuilder provides a high-level interface for retrieving nodes from
    Neo4j, supporting vector search, smart projections, and 'Live'
    hydration of results.

    Attributes:
        mapper: The AGMMapper used for loading model instances.
        model_class: The Python class representing the expected results.
    """

    def __init__(self, mapper: AGMMapper, model_class: type[T]):
        """Initializes the QueryBuilder.

        Args:
            mapper: An active AGMMapper instance.
            model_class: The model class to query and load.
        """
        self.mapper = mapper
        self.model_class = model_class
        self._resolve_live = False
        self._vector_search_params = None

    def resolve_live(self) -> "QueryBuilder[T]":
        """Enables live data hydration for the query results.

        When enabled, fields marked with @Live will be automatically
        populated via DI during the load phase.

        Returns:
            The QueryBuilder instance (fluent interface).
        """
        self._resolve_live = True
        return self

    def vector_search(self, vector_index: str, query_text: str, top_k: int = 5) -> "QueryBuilder[T]":
        """Configures the query to perform a vector similarity search.

        Args:
            vector_index: Name of the vector index in Neo4j.
            query_text: The search query string.
            top_k: Number of nearest neighbors to return.

        Returns:
            The QueryBuilder instance (fluent interface).
        """
        self._vector_search_params = {
            "index": vector_index,
            "query": query_text,
            "top_k": top_k,
        }
        return self

    def _generate_smart_projection(self) -> str:
        """Generates a Cypher map projection based on model type hints.

        Excludes @Live and @Rel fields from the initial database fetch
        to optimize performance and avoid unnecessary data retrieval.

        Returns:
            A Cypher map projection string (e.g., '{id: n.id, ...}').
        """
        hints = get_type_hints(self.model_class, include_extras=True)
        return_fields = []

        for field_name, field_type in hints.items():
            if get_origin(field_type) is Annotated:
                is_live = any(isinstance(m, Live) for m in get_args(field_type)[1:])
                is_rel = any(isinstance(m, Rel) for m in get_args(field_type)[1:])

                if not is_live and not is_rel:
                    return_fields.append(f"n.{field_name} AS {field_name}")
            else:
                return_fields.append(f"n.{field_name} AS {field_name}")

        if not return_fields:
            return "n"

        projection = "{" + ", ".join([f"{f.split(' AS ')[1]}: {f.split(' AS ')[0]}" for f in return_fields]) + "}"
        return projection

    async def execute(self, session: Any) -> list[T]:
        """Executes the query and returns a list of loaded model instances.

        Depending on configuration, this will perform either a standard
        MATCH query or a CALL to a vector index.

        Args:
            session: An active Neo4j driver session.

        Returns:
            A list of instantiated and optionally hydrated domain models.
        """
        label = self.model_class.__name__
        projection = self._generate_smart_projection()

        if self._vector_search_params:
            # Vector Search Cypher
            index_name = self._vector_search_params["index"]
            cypher_query = f"""
                CALL db.index.vector.queryNodes($index_name, $top_k, $quer  y)
                YIELD node AS n, score
                RETURN n {projection} AS data
            """
            logger.debug(f"Executing Vector Cypher:\n{cypher_query}")
            if hasattr(session, "run"):
                result = await session.run(
                    cypher_query,
                    index_name=index_name,
                    top_k=self._vector_search_params["top_k"],
                    query=self._vector_search_params["query"],
                )
                db_records = [record["data"] async for record in result]
            else:
                db_records = []
        else:
            # Default GET Cypher
            cypher_query = f"MATCH (n:{label})\nRETURN n {projection} AS data\nLIMIT 10"
            logger.debug(f"Executing Query Cypher:\n{cypher_query}")
            if hasattr(session, "run"):
                result = await session.run(cypher_query)
                db_records = [record["data"] async for record in result]
            else:
                db_records = []

        results = []
        for record in db_records:
            model = await self.mapper.load(self.model_class, record, resolve_live=self._resolve_live)
            results.append(model)

        return results
