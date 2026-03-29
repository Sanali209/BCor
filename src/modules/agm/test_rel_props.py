import pytest
import asyncio
from dataclasses import dataclass, field
from typing import Annotated, Optional
from neo4j import AsyncGraphDatabase

from src.modules.agm.metadata import Rel, RelMetadata, Unique
from src.modules.agm.mapper import AGMMapper

@dataclass
class EdgeProps:
    score: float = 0.0
    source: str = "test"

@dataclass
class TargetNode:
    id: Annotated[str, Unique()]
    name: str = "Target"

@dataclass
class SourceNode:
    id: Annotated[str, Unique()]
    # Relationship with properties
    targets: Annotated[
        list[TargetNode], 
        Rel(type="LINKED_TO", metadata=RelMetadata(EdgeProps))
    ] = field(default_factory=list)

@pytest.fixture
async def neo4j_driver():
    uri = "bolt://localhost:7687"
    auth = ("neo4j", "password")
    driver = AsyncGraphDatabase.driver(uri, auth=auth)
    
    # Wait for connection (simple retry)
    for _ in range(5):
        try:
            await driver.verify_connectivity()
            break
        except Exception:
            await asyncio.sleep(1)
    else:
        pytest.skip("Neo4j not available at localhost:7687")
        
    yield driver
    await driver.close()

@pytest.fixture
async def neo4j_session(neo4j_driver):
    async with neo4j_driver.session() as session:
        # Cleanup
        await session.run("MATCH (n:SourceNode) DETACH DELETE n")
        await session.run("MATCH (n:TargetNode) DETACH DELETE n")
        yield session

@pytest.mark.asyncio
async def test_relationship_properties_save(neo4j_session):
    from unittest.mock import MagicMock
    from src.core.messagebus import MessageBus
    from dishka import make_async_container
    
    container = make_async_container()
    message_bus = MagicMock(spec=MessageBus)
    mapper = AGMMapper(container, message_bus)
    
    # 1. Setup nodes
    target = TargetNode(id="target-1", name="Target 1")
    # For now, we take properties from the target_node if its attributes match the rel model
    target.score = 0.85
    target.source = "semantic"
    
    source = SourceNode(id="source-1", targets=[target])
    
    # 2. Save
    await mapper.save(source, session=neo4j_session)
    
    # 3. Verify in Neo4j
    result = await neo4j_session.run(
        "MATCH (s:SourceNode {id: 'source-1'})-[r:LINKED_TO]->(t:TargetNode {id: 'target-1'}) "
        "RETURN r.score as score, r.source as source"
    )
    record = await result.single()
    assert record is not None
    assert record["score"] == 0.85
    assert record["source"] == "semantic"
