import pytest
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass
from typing import Annotated

from src.modules.agm.mapper import AGMMapper
from src.modules.agm.metadata import Live

@dataclass
class MockNode:
    id: str
    name: str = ""
    status: Annotated[str, Live(handler=str)] = "offline"

@pytest.mark.asyncio
async def test_identity_map_consistency():
    """Verifies that multiple loads of the same node ID return the same object instance."""
    container = MagicMock()
    message_bus = MagicMock()
    mapper = AGMMapper(container, message_bus)
    
    record = {"id": "node-1", "name": "Test Node"}
    
    # First load
    node1 = await mapper.load(MockNode, record, resolve_live=False)
    # Second load
    node2 = await mapper.load(MockNode, record, resolve_live=False)
    
    assert node1 is node2
    assert node1.id == "node-1"

@pytest.mark.asyncio
async def test_smart_hydration_trigger():
    """Verifies that a cached node is hydrated only when resolve_live=True is requested."""
    container = AsyncMock()
    container.get.return_value = "online"
    message_bus = MagicMock()
    mapper = AGMMapper(container, message_bus)
    
    record = {"id": "node-1", "name": "Test Node"}
    
    # 1. Load without hydration
    node = await mapper.load(MockNode, record, resolve_live=False)
    assert node.status == "offline"
    container.get.assert_not_called()
    
    # 2. Load with hydration (should update the SAME instance)
    node_hydrated = await mapper.load(MockNode, record, resolve_live=True)
    
    assert node_hydrated is node
    assert node.status == "online"
    container.get.assert_called_once()
    
    # 3. Load again with hydration (should NOT call container again)
    await mapper.load(MockNode, record, resolve_live=True)
    container.get.assert_called_once()

@pytest.mark.asyncio
async def test_save_updates_identity_map():
    """Verifies that saving a node adds it to the identity map."""
    container = MagicMock()
    message_bus = MagicMock()
    message_bus.dispatch = AsyncMock()
    mapper = AGMMapper(container, message_bus)
    
    node = MockNode(id="node-saved", name="New Node")
    
    # Save the node
    await mapper.save(node)
    
    # Load the same node (should be from cache now)
    record = {"id": "node-saved", "name": "New Node"}
    loaded_node = await mapper.load(MockNode, record, resolve_live=False)
    
    assert loaded_node is node

@pytest.mark.asyncio
async def test_polymorphic_identity_map():
    """Verifies that identity map handles polymorphic subclasses consistently."""
    container = MagicMock()
    message_bus = MagicMock()
    mapper = AGMMapper(container, message_bus)
    
    @dataclass
    class BaseNode:
        id: str
    
    @dataclass
    class SpecializedNode(BaseNode):
        extra: str = ""

    mapper.register_subclass("Specialized", SpecializedNode)
    
    record = {"id": "poly-1", "labels": ["Specialized"], "extra": "data"}
    
    # Load via BaseNode, should get SpecializedNode
    node1 = await mapper.load(BaseNode, record)
    assert isinstance(node1, SpecializedNode)
    
    # Load again via BaseNode
    node2 = await mapper.load(BaseNode, record)
    assert node1 is node2
