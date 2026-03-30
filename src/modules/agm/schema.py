import logging
from typing import Annotated, Any, get_args, get_origin, get_type_hints, List, Dict, Optional
from neo4j import Driver
from src.modules.agm.metadata import Unique, Indexed, VectorIndex
from src.modules.agm.ui_metadata import Searchable, DisplayName, Column

logger = logging.getLogger(__name__)

class AGMSchemaManager:
    """Manages Neo4j constraints and indexes based on domain model annotations."""

    def __init__(self, driver: Driver):
        self.driver = driver

    async def sync_class(self, cls: type):
        """Discovers and creates constraints/indexes for a given class.
        
        Args:
            cls: The domain model class to inspect.
        """
        label = cls.__name__
        hints = get_type_hints(cls, include_extras=True)
        
        async with self.driver.session() as session:
            for field_name, field_type in hints.items():
                if get_origin(field_type) is not Annotated:
                    continue
                
                for metadata in get_args(field_type)[1:]:
                    if isinstance(metadata, Unique):
                        await self._create_unique_constraint(session, label, field_name)
                    elif isinstance(metadata, Indexed):
                        await self._create_range_index(session, label, field_name)
                    elif isinstance(metadata, VectorIndex):
                        await self._create_vector_index(session, label, field_name, metadata)

    def get_search_schema(self, classes: List[type]) -> List[Dict[str, Any]]:
        """Scans classes for Searchable fields and returns a GUI-ready schema.
        
        Args:
            classes: List of domain model classes to inspect.
            
        Returns:
            A list of searchable field definitions sorted by priority.
        """
        schema: Dict[str, Dict[str, Any]] = {}
        
        for cls in classes:
            # We use get_type_hints which handles MRO/inheritance.
            hints = get_type_hints(cls, include_extras=True)
            
            for field_name, field_type in hints.items():
                if get_origin(field_type) is not Annotated:
                    continue
                
                args = get_args(field_type)
                base_type = args[0]
                metadata = args[1:]
                
                search_meta = next((m for m in metadata if isinstance(m, Searchable)), None)
                if not search_meta:
                    continue
                
                # Extract DisplayName override or fallback to capitalized field name
                display_name = next((m.name for m in metadata if isinstance(m, DisplayName)), field_name.replace("_", " ").capitalize())
                
                # Consolidate if multiple classes share a field (keep highest priority / most specific)
                if field_name not in schema or search_meta.priority < schema[field_name]["priority"]:
                    schema[field_name] = {
                        "name": field_name,
                        "label": display_name,
                        "type": self._normalize_type(base_type),
                        "widget": search_meta.widget or self._guess_widget(base_type),
                        "priority": search_meta.priority,
                        "advanced": search_meta.advanced
                    }
        
        return sorted(schema.values(), key=lambda x: x["priority"])

    def _normalize_type(self, base_type: type) -> str:
        if base_type is int: return "int"
        if base_type is float: return "float"
        if base_type is str: return "str"
        if base_type is bool: return "bool"
        return str(base_type)

    def _guess_widget(self, base_type: type) -> str:
        """Heuristics to determine the best UI widget based on Python type."""
        type_str = str(base_type).lower()
        if base_type in (int, float): 
            return "range"
        if "list[float]" in type_str or "list[int]" in type_str:
            return "vector"
        if base_type is bool:
            return "checkbox"
        return "text"

    async def _create_unique_constraint(self, session, label: str, field: str):
        constraint_name = f"uniq_{label}_{field}"
        query = f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS FOR (n:{label}) REQUIRE n.{field} IS UNIQUE"
        logger.info(f"Ensuring uniqueness constraint: {constraint_name}")
        await session.run(query)

    async def _create_range_index(self, session, label: str, field: str):
        index_name = f"idx_{label}_{field}"
        query = f"CREATE INDEX {index_name} IF NOT EXISTS FOR (n:{label}) ON (n.{field})"
        logger.info(f"Ensuring range index: {index_name}")
        await session.run(query)

    async def _create_vector_index(self, session, label: str, field: str, meta: VectorIndex):
        index_name = f"vec_{label}_{field}"
        
        # Check if index already exists
        result = await session.run(f"SHOW INDEXES WHERE name = '{index_name}'")
        if await result.single():
            logger.debug(f"Vector index {index_name} already exists.")
            return

        # Use procedure for wider compatibility (Neo4j 5.x Community)
        query = (
            f"CALL db.index.vector.createNodeIndex("
            f"'{index_name}', '{label}', '{field}', "
            f"{meta.dims}, '{meta.metric.upper()}'"
            f")"
        )
        logger.info(f"Ensuring vector index: {index_name} ({meta.dims} dims, {meta.metric.upper()})")
        await session.run(query)
