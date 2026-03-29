import pytest
import uuid
from typing import Annotated, Optional
from dataclasses import dataclass
from neo4j import GraphDatabase
from src.modules.agm.metadata import Unique, Indexed, VectorIndex
import asyncio
from neo4j import AsyncGraphDatabase

@pytest.fixture
async def neo4j_driver():
    uri = "bolt://localhost:7687"
    auth = ("neo4j", "password")
    driver = AsyncGraphDatabase.driver(uri, auth=auth)
    
    # Wait for connection (simple retry)
    for _ in range(10):
        try:
            await driver.verify_connectivity()
            break
        except Exception:
            await asyncio.sleep(2)
    else:
        pytest.skip("Neo4j not available at localhost:7687")
        
    yield driver
    await driver.close()

from src.modules.agm.schema import AGMSchemaManager

@dataclass
class SchemaTestNode:
    id: Annotated[str, Unique()]
    email: Annotated[str, Indexed()]
    embedding: Annotated[list[float], VectorIndex(dims=128)]
    name: str = ""

@pytest.mark.asyncio
async def test_schema_manager_ensures_constraints(neo4j_driver):
    """Verifies that AGMSchemaManager executes the correct Cypher to create constraints."""
    manager = AGMSchemaManager(neo4j_driver)
    
    # We pass the class to the manager
    await manager.sync_class(SchemaTestNode)
    
    async with neo4j_driver.session() as session:
        # 1. Check uniqueness constraint
        result = await session.run("SHOW CONSTRAINTS")
        constraints = await result.data()
        assert any(c["labelsOrTypes"] == ["SchemaTestNode"] and c["properties"] == ["id"] and c["type"] == "UNIQUENESS" for c in constraints)
        
        # 2. Check range index
        result = await session.run("SHOW INDEXES")
        indexes = await result.data()
        assert any(idx["labelsOrTypes"] == ["SchemaTestNode"] and idx["properties"] == ["email"] and idx["type"] == "RANGE" for idx in indexes)
        
        # 3. Check vector index (using APOC or native depending on version, 5.x uses native)
        assert any(idx["labelsOrTypes"] == ["SchemaTestNode"] and idx["properties"] == ["embedding"] and idx["type"] == "VECTOR" for idx in indexes)
