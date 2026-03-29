import pytest
import asyncio
from typing import Annotated
from dataclasses import dataclass, field
from neo4j import AsyncGraphDatabase

from src.modules.agm.mapper import AGMMapper
from src.modules.agm.fluent import QueryBuilder
from src.modules.agm.metadata import Live

# 1. Define models for integration testing
@dataclass
class IntegrationNode:
    id: str
    name: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)

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

@pytest.fixture
async def neo4j_session(neo4j_driver):
    async with neo4j_driver.session() as session:
        # Cleanup before each test
        await session.run("MATCH (n:IntegrationNode) DETACH DELETE n")
        yield session

@pytest.mark.asyncio
async def test_full_roundtrip_with_neo4j(neo4j_session):
    """Verifies that a node can be saved and loaded back from a real Neo4j instance."""
    from dishka import make_async_container, Provider, Scope, provide
    from src.core.messagebus import MessageBus
    from unittest.mock import MagicMock
    
    # Setup dependencies
    container = make_async_container()
    message_bus = MagicMock(spec=MessageBus)
    message_bus.dispatch = asyncio.Future()
    message_bus.dispatch.set_result(None)
    
    mapper = AGMMapper(container, message_bus)
    
    # 1. Save
    node = IntegrationNode(id="int-1", name="Integration Test Node", description="Checking real DB", tags=["test", "neo4j"])
    await mapper.save(node, session=neo4j_session)
    
    # 2. Query/Load
    builder = QueryBuilder(mapper, IntegrationNode)
    # We simulate the record retrieval or use execute
    # Actually, let's use QueryBuilder.execute which we need to verify too
    
    # For execute to work, we need it to run a real query.
    # QueryBuilder.execute is currently a bit abstract in my memory, let me check it.
    results = await builder.execute(session=neo4j_session)
    
    assert len(results) >= 1
    loaded = results[0]
    assert loaded.id == "int-1"
    assert loaded.name == "Integration Test Node"
    assert loaded.tags == ["test", "neo4j"]
    
    # 3. Identity Map Check (Integration level)
    # Since it's the same mapper and same request, they should be 'is'
    loaded_again = await mapper.load(IntegrationNode, {"id": "int-1", "name": "..."})
    assert loaded_again is node
