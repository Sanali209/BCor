import pytest
import asyncio
from typing import Any
import os

from src.modules.agm.tasks import compute_stored_field

from neo4j import AsyncGraphDatabase
import pytest_asyncio

# --- Mock Domain Models ---
from dataclasses import dataclass

@dataclass
class MockTag:
    id: str
    name: str

# --- Mock Handler ---
class MockGraphHandler:
    async def run(self, source_value: Any, context: dict[str, Any] | None = None) -> Any:
        return [
            MockTag(id="tag-1", name="auto/wd_tag/cosplay"),
            MockTag(id="tag-2", name="auto/wd_tag/anime")
        ]

# --- Test Fixtures ---
@pytest_asyncio.fixture
async def neo4j_session():
    uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    auth = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
    async with AsyncGraphDatabase.driver(uri, auth=auth) as driver:
        async with driver.session() as session:
            await session.run("MATCH (n:TestAsset) DETACH DELETE n")
            await session.run("MATCH (n:Tag) DETACH DELETE n")
            await session.run("CREATE (:TestAsset {id: 'asset-1'})")
            
            yield session
            
            await session.run("MATCH (n:TestAsset) DETACH DELETE n")
            await session.run("MATCH (n:Tag) DETACH DELETE n")


@pytest.mark.asyncio
async def test_automatic_graph_serialization(neo4j_session):
    """
    Test Phase 1: Ensure that compute_stored_field can unroll dataclasses
    returned by a handler and create relationships using MERGE automatically.
    """
    from src.modules.assets.infrastructure.providers import AssetsInfrastructureProvider
    original_resolve = AssetsInfrastructureProvider().provide_handler_registry
    
    class FakeRegistry:
        def resolve(self, mime_type, handler_name):
            return MockGraphHandler()
            
    # Mock the registry for the test
    from unittest import mock
    with mock.patch('src.modules.assets.infrastructure.providers.AssetsInfrastructureProvider.provide_handler_registry', return_value=FakeRegistry()):
        # Pass metadata context that tells tasks.py this field is a Relationship
        test_context = {
            "agm_field_type": "RELATION",
            "rel_type": "HAS_TAG",
            "target_label": "Tag"
        }
        
        # Calling the taskiq underlying coroutine
        # Actually in TaskIQ we can use the original wrapped func or .coroutine
        await getattr(compute_stored_field, "coroutine", compute_stored_field)(
            node_id="asset-1",
            field_name="wd_tags",
            source_value="dummy",
            mime_type="*/*",
            handler="MockGraphHandler",
            context=test_context,
            priority=0
        )
        
        # Verification
        result = await neo4j_session.run(
            "MATCH (a:TestAsset {id: 'asset-1'})-[r:HAS_TAG]->(t:Tag) "
            "RETURN t.id as id, t.name as name ORDER BY t.name"
        )
        
        tags = []
        async for record in result:
             tags.append(dict(record))
        
        assert len(tags) == 2, f"Expected 2 Tags created via relation, got {len(tags)}"
        assert tags[0]["id"] == "tag-2"
        assert tags[0]["name"] == "auto/wd_tag/anime"
        assert tags[1]["id"] == "tag-1"
        assert tags[1]["name"] == "auto/wd_tag/cosplay"


@pytest.mark.asyncio
async def test_inference_event_creation(neo4j_session):
    """
    Test Phase 2: Ensure that compute_stored_field creates an InferenceEvent
    node for tracking inference completeness and logging hypotheses.
    """
    from src.modules.assets.infrastructure.providers import AssetsInfrastructureProvider
    original_resolve = AssetsInfrastructureProvider().provide_handler_registry
    
    class FakeRegistry:
        def resolve(self, mime_type, handler_name):
            # A handler that returns empty to verify EMPTY status
            class EmptyHandler:
                async def run(self, source_value: Any, context: dict[str, Any] | None = None) -> Any:
                    return None
            return EmptyHandler()
            
    from unittest import mock
    with mock.patch('src.modules.assets.infrastructure.providers.AssetsInfrastructureProvider.provide_handler_registry', return_value=FakeRegistry()):
        test_context = {
            "agm_field_type": "PROPERTY"
        }
        
        await getattr(compute_stored_field, "coroutine", compute_stored_field)(
            node_id="asset-1",
            field_name="dummy_field",
            source_value="dummy_input",
            mime_type="*/*",
            handler="EmptyHandler",
            context=test_context,
            priority=0
        )
        
        # Verification: we should have 1 InferenceEvent connected to Asset with status EMPTY
        result = await neo4j_session.run(
            "MATCH (a:TestAsset {id: 'asset-1'})-[r:HAS_INFERENCE]->(e:InferenceEvent) "
            "RETURN e.handler_name as handler_name, e.status as status"
        )
        
        events = []
        async for record in result:
             events.append(dict(record))
        
        assert len(events) == 1, f"Expected 1 InferenceEvent created, got {len(events)}"
        assert events[0]["handler_name"] == "EmptyHandler"
        assert events[0]["status"] == "EMPTY"


@pytest.mark.asyncio
async def test_smilingwolf_handler():
    from src.modules.assets.infrastructure.handlers.smilingwolf import SmilingWolfHandler
    from pathlib import Path
    
    # Path to test image (should be dynamically resolved but we know roughly where we are)
    test_image_dir = Path(__file__).parent.parent / "samples"
    test_image_path = test_image_dir / "test_diagnostic.webp"
    
    if not test_image_path.exists():
        pytest.skip(f"Test image not found at {test_image_path}")
        
    tags = await SmilingWolfHandler.run(uri=f"file://{str(test_image_path.resolve())}")
    
    assert tags is not None
    assert len(tags) > 0, "Expected tags to be generated from the test image"
    
    # Check that we have 1 character, 1 rating, and multiple gen tags
    ratings = [t.id for t in tags if "wd_rating" in t.id]
    chars = [t.id for t in tags if "wd_character" in t.id]
    gen = [t.id for t in tags if "wd_tag" in t.id]
    
    assert len(ratings) == 1, "Expected exactly 1 rating tag"
    
    print(f"Generated {len(tags)} tags.")
    print(f"Ratings: {ratings}")
    print(f"Gen Tags: {gen[:5]}...")


@pytest.mark.asyncio
async def test_smilingwolf_graph_integration(neo4j_session):
    """
    Test Phase 3: Ensure compute_stored_field integrates with SmilingWolfHandler
    to actually create :InferenceEvent and :Tag nodes in the Neo4j database.
    """
    from src.modules.assets.infrastructure.providers import AssetsInfrastructureProvider
    from pathlib import Path

    # Use the real registry but check the path constraint
    test_image_dir = Path(__file__).parent.parent / "samples"
    test_image_path = test_image_dir / "test_diagnostic.webp"
    if not test_image_path.exists():
        pytest.skip("No test image found")

    test_context = {
        "agm_field_type": "RELATION",
        "rel_type": "HAS_TAG",
        "target_label": "Tag"
    }

    # Execute the actual worker coroutine
    await getattr(compute_stored_field, "coroutine", compute_stored_field)(
        node_id="asset-1",
        field_name="wd_tags",
        source_value=f"file://{str(test_image_path.resolve())}",
        mime_type="*/*",
        handler="SmilingWolfHandler",
        context=test_context,
        priority=0
    )

    # 1. Verify InferenceEvent was created successfully
    events_res = await neo4j_session.run(
        "MATCH (a:TestAsset {id: 'asset-1'})-[r:HAS_INFERENCE]->(e:InferenceEvent) RETURN e.status as status"
    )
    events = [dict(record) async for record in events_res]
    assert len(events) == 1, "Should have 1 inference event"
    assert events[0]["status"] == "SUCCESS", f"Inference failed: {events[0]}"

    # 2. Verify HAS_TAG relationships
    tags_res = await neo4j_session.run(
        "MATCH (a:TestAsset {id: 'asset-1'})-[r:HAS_TAG]->(t:Tag) RETURN t.id as id ORDER BY t.id"
    )
    tags = [dict(record) async for record in tags_res]
    assert len(tags) > 0, "Expected tags to be associated in graph"
    print(f"Graph Integration created {len(tags)} tags via HAS_TAG")


@pytest.mark.asyncio
async def test_on_complete_cascade(neo4j_session):
    """
    Test Phase 4: Ensure @OnComplete triggers only after ALL required
    InferenceEvents are in SUCCESS/EMPTY state.
    """
    from src.modules.assets.infrastructure.providers import AssetsInfrastructureProvider
    from unittest import mock
    
    # 1. Prepare node and CLEAN EVERYTHING
    await neo4j_session.run("MATCH (n:CompletionTestAsset) DETACH DELETE n")
    await neo4j_session.run("MATCH (e:InferenceEvent) WHERE e.asset_id = 'asset-test-1' DETACH DELETE e")
    await neo4j_session.run("CREATE (:CompletionTestAsset {id: 'asset-test-1'})")
    
    # Define a custom action handler state
    action_called_count = 0
    
    class ActionHandler:
        async def run(self, val: Any, context: dict[str, Any] | None = None) -> Any:
            nonlocal action_called_count
            action_called_count += 1
            return "DONE"

    class FakeRegistry:
        def resolve(self, mime_type, handler_name):
            if handler_name == "ActionHandler":
                return ActionHandler()
            class DefaultHandler:
                async def run(self, val, ctx=None): return "val"
            return DefaultHandler()
    
    with mock.patch('src.modules.assets.infrastructure.providers.AssetsInfrastructureProvider.provide_handler_registry', return_value=FakeRegistry()):
        # 1. Run for Field A: field_a
        await getattr(compute_stored_field, "coroutine", compute_stored_field)(
            node_id="asset-test-1",
            field_name="field_a",
            source_value="val_a",
            handler="HandlerA",
            context={"agm_field_type": "PROPERTY"},
        )
        
        # Diagnostic check if it fails
        if action_called_count != 0:
            events = await neo4j_session.run("MATCH (e:InferenceEvent {asset_id: 'asset-test-1'}) RETURN e.field_name, e.status")
            records = [record async for record in events]
            print(f"DEBUG: Events in graph: {records}")

        assert action_called_count == 0, f"Action should NOT be called after only 1 of 2 fields done. Called: {action_called_count}"
        
        # 2. Run for Field B: field_b
        await getattr(compute_stored_field, "coroutine", compute_stored_field)(
            node_id="asset-test-1",
            field_name="field_b",
            source_value="val_b",
            handler="HandlerB",
            context={"agm_field_type": "PROPERTY"},
        )
        
        assert action_called_count == 1, f"ActionHandler should have been called now (Actual: {action_called_count})"
