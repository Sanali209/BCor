import pytest
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass
from typing import Annotated

from src.modules.agm.mapper import AGMMapper
from src.modules.agm.query import CypherQuery

@dataclass
class MockUser:
    __label__ = "User"
    name: str
    age: int
    id: str = None

@pytest.fixture
def mapper():
    return AGMMapper(container=MagicMock(), message_bus=MagicMock())

def test_cypher_generation_basic(mapper):
    """Verify primary Cypher generation with filters."""
    query = CypherQuery(mapper, MockUser).where(name="Alice", age=30)
    cypher, params = query.build_cypher()
    
    assert "MATCH (n:User)" in cypher
    assert "WHERE n.name = $p_name AND n.age = $p_age" in cypher
    assert params == {"p_name": "Alice", "p_age": 30}

def test_cypher_generation_pagination(mapper):
    """Verify pagination and ordering."""
    query = CypherQuery(mapper, MockUser).order_by("name").skip(10).limit(5)
    cypher, params = query.build_cypher()
    
    assert "ORDER BY n.name" in cypher
    assert "SKIP 10" in cypher
    assert "LIMIT 5" in cypher

@pytest.mark.asyncio
async def test_query_execution_mapping(mapper):
    """Verify that results from session.run are correctly mapped to domain objects."""
    session = AsyncMock()
    
    # Mock Neo4j result data
    mock_node = {"name": "Alice", "age": 30}
    mock_record = {
        "n": mock_node,
        "labels": ["User"],
        "id": "user_123"
    }
    
    # Mock session.run().data()
    mock_result = AsyncMock()
    mock_result.data.return_value = [mock_record]
    session.run.return_value = mock_result
    
    # Mock mapper.load
    with mock.patch.object(mapper, "load", new_callable=AsyncMock) as mock_load:
        mock_load.return_value = MockUser(name="Alice", age=30, id="user_123")
        
        users = await mapper.query(MockUser).where(name="Alice").all(session)
        
        assert len(users) == 1
        assert users[0].name == "Alice"
        assert users[0].id == "user_123"
        
        # Verify mapper.load was called with correct data
        mock_load.assert_awaited_once()
        args = mock_load.call_args[0]
        assert args[0] == MockUser
        assert args[1]["id"] == "user_123"
        assert args[1]["name"] == "Alice"

import unittest.mock as mock
