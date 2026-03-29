import pytest
from typing import Annotated
from dataclasses import dataclass, field
from src.apps.asset_explorer.presentation.viewmodels.metadata import MetadataViewModel, PropertyDescriptor
from src.modules.agm.metadata import Stored, Rel, Unique
from src.modules.agm.ui_metadata import DisplayName, Hidden

@dataclass
class MockAsset:
    id: Annotated[str, Unique(), Hidden()]
    name: Annotated[str, DisplayName("Asset Name")] = "Test"
    caption: Annotated[str, DisplayName("BLIP Caption"), Stored(source_field="uri", handler="BLIP")] = ""
    tags: Annotated[list[str], Rel(type="HAS_TAG")] = field(default_factory=list)

def test_metadata_vm_introspection():
    asset = MockAsset(id="123", name="My Image", caption="A forest", tags=["nature"])
    vm = MetadataViewModel(asset)
    
    descriptors = vm.descriptors
    
    # Verify Hidden fields are filtered out
    assert "id" not in [d.name for d in descriptors]
    
    # Verify DisplayName is used
    name_desc = next(d for d in descriptors if d.id == "name")
    assert name_desc.display_name == "Asset Name"
    assert name_desc.value == "My Image"
    
    # Verify Stored field detection
    caption_desc = next(d for d in descriptors if d.id == "caption")
    assert caption_desc.is_stored is True
    assert caption_desc.handler == "BLIP"
    
    # Verify Rel field detection
    tags_desc = next(d for d in descriptors if d.id == "tags")
    assert tags_desc.is_relation is True
    assert tags_desc.rel_type == "HAS_TAG"

def test_metadata_vm_updates():
    asset = MockAsset(id="123", name="Old Name")
    vm = MetadataViewModel(asset)
    
    received_updates = []
    vm.property_changed.connect(lambda name, val: received_updates.append((name, val)))
    
    # Update value through VM
    vm.update_property("name", "New Name")
    
    assert asset.name == "New Name"
    assert len(received_updates) == 1
    assert received_updates[0] == ("name", "New Name")
