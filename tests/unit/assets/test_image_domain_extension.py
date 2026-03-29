import pytest
from src.modules.assets.domain.models import ImageAsset, SimilarTo, RelationType

def test_relation_type_enum():
    assert RelationType.DUPLICATE == "DUPLICATE"
    assert RelationType.NOT_DUPLICATE == "NOT_DUPLICATE"
    assert len(RelationType) == 9

def test_similar_to_defaults():
    sim = SimilarTo(id="target_id")
    assert sim.id == "target_id"
    assert sim.score == 1.0
    assert sim.distance == 0.0
    assert sim.relation_type == "NEW_MATCH"
    assert sim.engine == "semantic"

def test_image_asset_extension():
    asset = ImageAsset(
        id="test_id",
        uri="file://test.jpg",
        name="test.jpg",
        mime_type="image/jpeg",
        description="",
        content_hash="abc"
    )
    assert hasattr(asset, "perceptual_hash")
    assert hasattr(asset, "clip_embedding")
    assert hasattr(asset, "blip_embedding")
    assert asset.perceptual_hash == ""
    assert asset.clip_embedding == []
    assert asset.blip_embedding == []
