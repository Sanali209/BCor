import pytest
from uuid import uuid4
from src.modules.agm.mapper import AGMMapper
from src.modules.assets.domain.models import (
    SmartAlbum, 
    ImageAsset, 
    BoundingBoxAnnotation, 
    CaptionAnnotation
)
from unittest.mock import MagicMock

@pytest.fixture
def mapper():
    return AGMMapper(container=MagicMock(), message_bus=MagicMock())

@pytest.mark.asyncio
async def test_smart_album_criteria_serialization(mapper):
    """Verify that SmartAlbum criteria (dict) is correctly serialized via Adaptix."""
    criteria = {"mime": "image/*", "tags": ["vacation"]}
    album = SmartAlbum(id="a1", name="Vacation", filter_criteria=criteria)
    
    # 1. Dump (Structural Mapping)
    dumped = mapper.retort.dump(album)
    # filter_criteria should still be a dict at the structural level
    assert dumped["filter_criteria"] == criteria
    
    # 2. Restoration
    # Simulate DB record (where it was stringified for transport, then pre-parsed by load)
    record = {
        "id": "a1",
        "name": "Vacation",
        "filter_criteria": criteria, # pre-parsed by _load_instance
        "labels": ["SmartAlbum"]
    }
    
    restored = await mapper.load(SmartAlbum, record)
    assert restored.filter_criteria == criteria
    assert isinstance(restored.filter_criteria, dict)

@pytest.mark.asyncio
async def test_annotation_polymorphism_serialization(mapper):
    """Verify that polymorphic annotations are correctly serialized."""
    asset_id = "asset_1"
    bbox = BoundingBoxAnnotation(
        id="ann_1", 
        asset_id=asset_id, 
        x=0.1, y=0.1, w=0.5, h=0.5, 
        class_label="cat"
    )
    caption = CaptionAnnotation(
        id="ann_2", 
        asset_id=asset_id, 
        text="A cute cat"
    )
    
    # Verify BBox
    dumped_bbox = mapper.retort.dump(bbox)
    assert dumped_bbox["class_label"] == "cat"
    assert dumped_bbox["x"] == 0.1
    
    # Verify Caption
    dumped_caption = mapper.retort.dump(caption)
    assert dumped_caption["text"] == "A cute cat"
    
    # Verify Restoration
    restored_bbox = await mapper.load(BoundingBoxAnnotation, {**dumped_bbox, "labels": ["BoundingBoxAnnotation"]})
    assert isinstance(restored_bbox, BoundingBoxAnnotation)
    assert restored_bbox.class_label == "cat"
