from typing import (
    TypeVar,
    Generic,
    Type,
    Any,
    get_type_hints,
    Annotated,
    get_origin,
    get_args,
)
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.metadata import Live, Rel
from loguru import logger

T = TypeVar("T")


class QueryBuilder(Generic[T]):
    def __init__(self, mapper: AGMMapper, model_class: Type[T]):
        self.mapper = mapper
        self.model_class = model_class
        self._resolve_live = False
        self._vector_search_params = None

    def resolve_live(self) -> "QueryBuilder[T]":
        """Enable live data hydration from NATS/Bubus."""
        self._resolve_live = True
        return self

    def vector_search(
        self, vector_index: str, query_text: str, top_k: int = 5
    ) -> "QueryBuilder[T]":
        """Setup vector search parameters."""
        self._vector_search_params = {
            "index": vector_index,
            "query": query_text,
            "top_k": top_k,
        }
        return self

    def _generate_smart_projection(self) -> str:
        hints = get_type_hints(self.model_class, include_extras=True)
        return_fields = []

        for field_name, field_type in hints.items():
            if get_origin(field_type) is Annotated:
                is_live = any(isinstance(m, Live) for m in get_args(field_type)[1:])
                is_rel = any(isinstance(m, Rel) for m in get_args(field_type)[1:])

                # Exclude live fields from database projection
                if not is_live and not is_rel:
                    return_fields.append(f"n.{field_name} AS {field_name}")
            else:
                return_fields.append(f"n.{field_name} AS {field_name}")

        if not return_fields:
            return "n"

        # Return fields as JSON map projection `{field1: n.field1, ...}`
        projection = (
            "{"
            + ", ".join(
                [f"{f.split(' AS ')[1]}: {f.split(' AS ')[0]}" for f in return_fields]
            )
            + "}"
        )
        return projection

    async def execute(self, session: Any) -> list[T]:
        # Cypher execution using provided session
        label = self.model_class.__name__
        projection = self._generate_smart_projection()

        if self._vector_search_params:
            # Vector Search Cypher
            index_name = self._vector_search_params["index"]
            cypher_query = f"""
CALL db.index.vector.queryNodes($index_name, $top_k, $query)
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
            model = await self.mapper.load(
                self.model_class, record, resolve_live=self._resolve_live
            )
            results.append(model)

        return results
