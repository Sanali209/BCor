import logging
from typing import Annotated, Any, get_args, get_origin, get_type_hints
from neo4j import Driver
from src.modules.agm.metadata import Unique, Indexed, VectorIndex

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
        # Signature: createNodeIndex(indexName, label, propertyKey, dimensions, similarityFunction)
        query = (
            f"CALL db.index.vector.createNodeIndex("
            f"'{index_name}', '{label}', '{field}', "
            f"{meta.dims}, '{meta.metric.upper()}'"
            f")"
        )
        logger.info(f"Ensuring vector index: {index_name} ({meta.dims} dims, {meta.metric.upper()})")
        await session.run(query)
