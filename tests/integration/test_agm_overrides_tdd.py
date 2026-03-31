import pytest
import asyncio
from typing import Any
import os
from unittest import mock
from dataclasses import dataclass, field
from typing import Annotated

from src.modules.agm.metadata import Stored, Rel
from src.modules.agm.mapper import AGMMapper
from src.modules.assets.domain.models import Asset, ImageAsset, Tag

# --- Mock Handlers ---

class MockBlipHandler:
    async def run(self, uri: str, context: dict[str, Any] | None = None) -> str:
        return "BLIP: A generic asset description"

class MockOllamaHandler:
    async def run(self, uri: str, context: dict[str, Any] | None = None) -> str:
        return "Ollama: A beautiful image description"

class MockExifHandler:
    async def run(self, uri: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "f_number": 2.8,
            "iso": 100,
            "camera_make": "Sony"
        }

# --- Test ---

from src.modules.agm.messages import SyncFieldInfo, NodeSyncRequested

@pytest.mark.asyncio
async def test_polymorphic_metadata_overrides():
    """
    TDD Phase 1: Verify that AGMMapper uses the correct handler for 
    overridden fields in subclasses.
    """
    # 1. Setup Models
    generic_asset = Asset(id="gen-1", uri="file://generic.txt")
    image_asset = ImageAsset(id="img-1", uri="file://image.jpg")
    
    # 2. Mock MessageBus
    bus = mock.AsyncMock()
    mapper = AGMMapper(container=mock.Mock(), message_bus=bus, schema_manager=mock.Mock())
    
    # Trigger side effects for generic asset
    await mapper._handle_side_effects(generic_asset, previous_state={}, session=None)
    
    # Extract the NodeSyncRequested event from the bus calls
    gen_event = next(c.args[0] for c in bus.dispatch.call_args_list if isinstance(c.args[0], NodeSyncRequested) and c.args[0].node_id == "gen-1")
    gen_desc = next(f for f in gen_event.fields if f.field_name == "description")
    assert gen_desc.handler == "BLIP"

    # Trigger for image asset
    await mapper._handle_side_effects(image_asset, previous_state={}, session=None)
    img_event = next(c.args[0] for c in bus.dispatch.call_args_list if isinstance(c.args[0], NodeSyncRequested) and c.args[0].node_id == "img-1")
    img_desc = next(f for f in img_event.fields if f.field_name == "description")
    assert img_desc.handler == "OllamaHandler"

@pytest.mark.asyncio
async def test_exif_dictionary_unpacking():
    """
    TDD Phase 2: Verify that a single handler result (dict) can be unpacked 
    into multiple node properties in Neo4j.
    """
    from src.modules.agm.infrastructure.repositories.neo4j_metadata import Neo4jMetadataRepository
    
    repo = Neo4jMetadataRepository(uri="bolt://mock", auth=("u", "p"))
    repo.driver = mock.AsyncMock()
    
    results = [
        {
            "field": "f_number",
            "status": "SUCCESS",
            "result": {"f_number": 2.8, "iso": 100, "camera_make": "Sony"},
            "handler": "Pyexiv2Smart",
            "agm_field_type": "PROPERTY"
        }
    ]
    
    mock_tx = mock.AsyncMock()
    # Call the internal transaction logic manually for verification
    await repo._persist_batch_tx(mock_tx, node_id="img-1", event_id="evt-1", results=results, model_name="ImageAsset")
    
    # Verify properties
    queries = [c.args[0] for c in mock_tx.run.call_args_list]
    prop_sets = [q for q in queries if "SET n." in q]
    
    assert any("SET n.f_number" in q for q in prop_sets)
    assert any("SET n.iso" in q for q in prop_sets)
    assert any("SET n.camera_make" in q for q in prop_sets)
