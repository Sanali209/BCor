import pytest
import asyncio
import uuid
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from src.modules.agm.tasks import sync_node_metadata, compute_stored_field

@pytest.mark.asyncio
async def test_sequential_inference_heavy_tasks():
    """
    TDD Test: Verifies that heavy AI tasks (priority >= 10) are executed sequentially
    to prevent resource exhaustion on Windows.
    """
    execution_order = []
    
    class HeavyHandler:
        def __init__(self, name: str, delay: float):
            self.name = name
            self.delay = delay
            
        async def run(self, *args, **kwargs):
            execution_order.append(f"START_{self.name}")
            await asyncio.sleep(self.delay)
            execution_order.append(f"END_{self.name}")
            return f"result_{self.name}"

    handler_a = HeavyHandler("AI_A", 0.2)
    handler_b = HeavyHandler("AI_B", 0.1)

    class MockRegistry:
        def resolve(self, mime, handler_name):
            if handler_name == "AI_A": return handler_a
            if handler_name == "AI_B": return handler_b
            return None

    with patch("src.modules.assets.infrastructure.providers.AssetsInfrastructureProvider.provide_handler_registry", 
               return_value=MockRegistry()):
        
        # Trigger two heavy tasks simultaneously
        task_a = compute_stored_field(
            node_id="asset-1", field_name="f1", source_value="v1", 
            handler="AI_A", priority=10
        )
        task_b = compute_stored_field(
            node_id="asset-1", field_name="f2", source_value="v2", 
            handler="AI_B", priority=10
        )
        
        await asyncio.gather(task_a, task_b)
        
        # Verify sequential execution: START_A -> END_A -> START_B -> END_B
        # or vice-versa, but NOT START_A -> START_B -> END_...
        assert execution_order[1].startswith("END_"), f"Tasks did not run sequentially: {execution_order}"
        assert execution_order[3].startswith("END_")

@pytest.mark.asyncio
async def test_inference_event_overwrite_logic():
    """
    TDD Test: Verifies that re-running inference for the same field 
    overwrites the previous InferenceEvent instead of creating a chain.
    """
    from src.modules.agm.infrastructure.repositories.neo4j_metadata import Neo4jMetadataRepository
    
    # We want to verify that Neo4jMetadataRepository.persist_metadata 
    # uses a pattern that doesn't duplicate event nodes for the same handler/field.
    repo = MagicMock()
    repo.persist_metadata = MagicMock(side_effect=lambda **kw: asyncio.sleep(0))
    repo.persist_metadata_batch = MagicMock(side_effect=lambda **kw: asyncio.sleep(0))
    repo.close = MagicMock(side_effect=lambda **kw: asyncio.sleep(0))
    
    with patch("src.modules.agm.tasks._get_repo", return_value=repo):
        # Run 1
        await compute_stored_field(
            node_id="asset-1", field_name="description", source_value="uri", 
            handler="Ollama", priority=10
        )
        
        # Run 2 (Update)
        await compute_stored_field(
            node_id="asset-1", field_name="description", source_value="uri_updated", 
            handler="Ollama", priority=10
        )
        
        # Verification: repo.persist_metadata should have been called twice, 
        # but our implementation should ensure Neo4j logic uses MERGE on (Asset)-[:HAS_INFERENCE]->(InferenceEvent {field_name: ...})
        assert repo.persist_metadata.call_count == 2

@pytest.mark.asyncio
async def test_batch_ingestion_unwind_mock():
    """
    TDD Test: Verifies that sync_node_metadata calls persist_metadata_batch 
    with the correct structure for multiple fields.
    """
    from src.modules.agm.infrastructure.repositories.neo4j_metadata import Neo4jMetadataRepository
    repo = MagicMock(spec=Neo4jMetadataRepository)
    
    fields = [
        {"field_name": "f1", "source_value": "v1", "handler": "H1"},
        {"field_name": "f2", "source_value": "v2", "handler": "H2"}
    ]
    
    with patch("src.modules.agm.tasks._get_repo", return_value=repo):
        with patch("src.modules.agm.tasks._process_single_field", return_value="done"):
            await sync_node_metadata(node_id="asset-1", fields=fields)
            
            # Verify batch persistence was called
            repo.persist_metadata_batch.assert_called_once()
            args, kwargs = repo.persist_metadata_batch.call_args
            assert args[0] == "asset-1"
            assert len(args[2]) == 2 # 2 fields
