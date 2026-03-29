import pytest
from dataclasses import dataclass, field
from typing import Annotated, Optional
import json
from datetime import datetime
from uuid import UUID, uuid4

from unittest.mock import AsyncMock, MagicMock
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.metadata import Stored, Rel

@dataclass
class NestedData:
    key: str
    value: int

@dataclass
class ComplexModel:
    id: str
    name: str
    data: dict = field(default_factory=dict)
    metadata: Optional[NestedData] = None
    created_at: datetime = field(default_factory=datetime.now)
    uid: UUID = field(default_factory=uuid4)

@pytest.fixture
def mapper():
    return AGMMapper(container=MagicMock(), message_bus=MagicMock())

@pytest.mark.asyncio
async def test_adaptix_serialization_flattening(mapper):
    """Test that Adaptix correctly serializes complex types for Neo4j."""
    uid = UUID("550e8400-e29b-41d4-a716-446655440000")
    now = datetime(2026, 3, 26, 15, 0, 0)
    model = ComplexModel(
        id="cm_1",
        name="Test",
        data={"a": 1},
        metadata=NestedData(key="k", value=10),
        created_at=now,
        uid=uid
    )
    
    # We'll use a mock session to inspect the parameters passed to save
    session = AsyncMock()
    # Mock return for run().data() as save() returns the result
    session.run.return_value.data.return_value = [{"n": {"id": "cm_1"}}]
    
    await mapper.save(model, session=session)
    
    # Verify parameters
    args, kwargs = session.run.call_args
    # cypher_params was passed as args[1]
    params = args[1] if len(args) > 1 else kwargs.get("parameters", {})
    
    # Check that session.run was called with correct stringified params
    assert params["data"] == '{"a": 1}'
    assert params["metadata"] == '{"key": "k", "value": 10}'
    assert params["uid"] == str(uid)
    assert params["created_at"] == now.isoformat()

@pytest.mark.asyncio
async def test_adaptix_deserialization(mapper):
    """Test that Adaptix correctly restores complex types from Neo4j records."""
    record = {
        "id": "cm_1",
        "name": "Test",
        "data": '{"a": 1}',
        "metadata": '{"key": "k", "value": 10}',
        "created_at": "2026-03-26T15:00:00",
        "uid": "550e8400-e29b-41d4-a716-446655440000",
        "labels": ["ComplexModel"]
    }
    
    instance = await mapper.load(ComplexModel, record)
    
    assert instance.name == "Test"
    assert instance.data == {"a": 1}
    assert instance.metadata.key == "k"
    assert instance.uid == UUID("550e8400-e29b-41d4-a716-446655440000")
