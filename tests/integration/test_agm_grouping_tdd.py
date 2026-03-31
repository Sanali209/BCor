import pytest
import asyncio
from typing import Any, Annotated, List, Dict
from unittest import mock
from dataclasses import dataclass, field

from src.modules.agm.metadata import Stored, Rel
from src.modules.agm.messages import SyncFieldInfo, NodeSyncRequested
from src.modules.agm.mapper import AGMMapper
from src.modules.assets.domain.models import Asset

# --- Mock Model for Grouping ---

@dataclass
class ExifAsset(Asset):
    f_number: Annotated[float, Stored(source_field="uri", handler="Pyexiv2Smart")] = 0.0
    iso: Annotated[int, Stored(source_field="uri", handler="Pyexiv2Smart")] = 0
    camera: Annotated[str, Stored(source_field="uri", handler="Pyexiv2Smart")] = ""

# --- Test ---

@pytest.mark.asyncio
async def test_handler_grouping_logic():
    """
    TDD Phase 1: Verify that AGMMapper groups multiple fields sharing 
    the same handler into a single SyncFieldInfo.
    """
    # 1. Setup
    asset = ExifAsset(id="exif-1", uri="file://photo.jpg")
    bus = mock.AsyncMock()
    mapper = AGMMapper(container=mock.Mock(), message_bus=bus, schema_manager=mock.Mock())
    
    # 2. Trigger side effects (f_number, iso, camera all changed from default)
    # Actually they are defaults, let's pretend we just ingested them
    await mapper._handle_side_effects(asset, previous_state={}, session=None)
    
    # 3. Verify dispatch
    # Extract the NodeSyncRequested event
    event = next(c.args[0] for c in bus.dispatch.call_args_list if isinstance(c.args[0], NodeSyncRequested))
    
    # Check that there is a group with Pyexiv2Smart
    exif_group = next((f for f in event.fields if f.handler == "Pyexiv2Smart"), None)
    assert exif_group is not None, "Pyexiv2Smart group missing"
    
    # Check context for shared fields tracking
    shared = exif_group.context_metadata.get("shared_fields", [])
    assert "f_number" in shared
    assert "iso" in shared
    assert "camera" in shared
    
    # Ensure there isn't more than one Pyexiv2Smart task
    assert len([f for f in event.fields if f.handler == "Pyexiv2Smart"]) == 1

@pytest.mark.asyncio
async def test_shared_event_propagation_in_tasks():
    """
    TDD Phase 2: Verify that tasks.py correctly expands a grouped field 
    into multiple results for persistence.
    """
    from src.modules.agm.tasks import sync_node_metadata
    
    # Mock Repository
    mock_repo = mock.AsyncMock()
    with mock.patch('src.modules.agm.tasks._get_repo', return_value=mock_repo):
        with mock.patch('src.modules.agm.tasks._process_single_field', return_value={"f_number": 2.8, "iso": 400}):
            
            # Simulate a grouped field request
            fields = [
                {
                    "field_name": "f_number",
                    "source_value": "file://photo.jpg",
                    "handler": "Pyexiv2Smart",
                    "context_metadata": {
                        "shared_fields": ["f_number", "iso", "camera"],
                        "agm_field_type": "PROPERTY"
                    }
                }
            ]
            
            await sync_node_metadata(node_id="exif-1", fields=fields)
            
            # Verify that persist_metadata_batch receives 3 results
            batch_call = mock_repo.persist_metadata_batch.call_args
            results = batch_call.args[2]
            
            field_names = [r["field"] for r in results]
            assert "f_number" in field_names
            assert "iso" in field_names
            assert "camera" in field_names
            
            # All shared fields should have the same (dict) result to trigger UNPACKING
            for r in results:
                assert isinstance(r["result"], dict)
                assert r["result"]["f_number"] == 2.8
