import pytest
import asyncio
from typing import Annotated
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock
from src.modules.agm.metadata import Unique, Indexed, VectorIndex
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.schema import AGMSchemaManager

@dataclass
class DummyModel:
    id: Annotated[str, Unique()]
    name: Annotated[str, Indexed()]
    vector: Annotated[list[float], VectorIndex(dims=128)] = None

@pytest.mark.asyncio
async def test_agm_auto_schema_sync_on_registration():
    """
    TDD Test: Verifies that when a subclass is registered with AGMMapper,
    the AGMSchemaManager is called to sync the class schema.
    """
    # 1. Setup mocks
    mock_container = MagicMock()
    mock_bus = MagicMock()
    mock_schema_manager = AsyncMock(spec=AGMSchemaManager)
    
    mapper = AGMMapper(
        container=mock_container,
        message_bus=mock_bus,
        schema_manager=mock_schema_manager
    )
    
    # 2. Register a new subclass
    await mapper.register_subclass("Dummy", DummyModel)
    
    # 3. Verify sync_class was called for DummyModel
    mock_schema_manager.sync_class.assert_called_once_with(DummyModel)

@pytest.mark.asyncio
async def test_schema_manager_generates_correct_cypher():
    """
    TDD Test: Verifies that AGMSchemaManager generates correct Cypher 
    queries for Unique, Indexed, and VectorIndex annotations.
    """
    mock_driver = MagicMock()
    mock_session = AsyncMock()
    mock_driver.session.return_value.__aenter__.return_value = mock_session
    
    # Mock SHOW INDEXES for vector check (return nothing)
    mock_result = AsyncMock()
    mock_result.single.return_value = None
    mock_session.run.side_effect = [
        None, # Unique constraint
        None, # Range index
        mock_result, # SHOW INDEXES call
        None  # Vector index call
    ]
    
    manager = AGMSchemaManager(driver=mock_driver)
    
    # Run sync
    await manager.sync_class(DummyModel)
    
    # Verify Cypher queries
    calls = [call.args[0] for call in mock_session.run.call_args_list]
    
    # Uniqueness constraint
    assert any("CREATE CONSTRAINT uniq_DummyModel_id" in c for c in calls)
    assert any("REQUIRE n.id IS UNIQUE" in c for c in calls)
    
    # Range index
    assert any("CREATE INDEX idx_DummyModel_name" in c for c in calls)
    assert any("ON (n.name)" in c for c in calls)
    
    # Vector index (using procedure CALL db.index.vector.createNodeIndex)
    assert any("CALL db.index.vector.createNodeIndex" in c for c in calls)
    assert any("'vec_DummyModel_vector', 'DummyModel', 'vector', 128" in c for c in calls)
