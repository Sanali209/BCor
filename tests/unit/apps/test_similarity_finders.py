import pytest
from unittest.mock import MagicMock, AsyncMock
from src.apps.experemental.declarative_imgededupe.services import PHashFinder, VectorFinder
from src.modules.assets.domain.models import ImageAsset

@pytest.fixture
def mock_mapper():
    return MagicMock()

@pytest.fixture
def sample_assets():
    return [
        ImageAsset(id="a1", uri="file://1.jpg", name="1", mime_type="image/jpeg", description="", content_hash="h1", perceptual_hash="f000"),
        ImageAsset(id="a2", uri="file://2.jpg", name="2", mime_type="image/jpeg", description="", content_hash="h2", perceptual_hash="f001"),
        ImageAsset(id="a3", uri="file://3.jpg", name="3", mime_type="image/jpeg", description="", content_hash="h3", perceptual_hash="0000"),
    ]

@pytest.mark.timeout(30)
@pytest.mark.asyncio
async def test_phash_finder_finds_near_duplicates(sample_assets):
    """PHashFinder should find assets with Hamming distance <= threshold."""
    finder = PHashFinder(threshold=2)  # threshold in bits/distance
    
    # Distance f000 to f001 is 1 bit (Hamming distance)
    # We expect a1 to be similar to a2
    results = await finder.find_pairs(sample_assets)
    
    # results should be a list of (asset_a, asset_b, distance)
    assert len(results) >= 1
    found = False
    for a, b, dist in results:
        if (a.id == "a1" and b.id == "a2") or (a.id == "a2" and b.id == "a1"):
            found = True
            assert dist <= 2
    assert found

@pytest.mark.timeout(30)
@pytest.mark.asyncio
async def test_vector_finder_calls_mapper_search(mock_mapper):
    """VectorFinder should offload search to AGMMapper.vector_search()."""
    finder = VectorFinder(mapper=mock_mapper, embedding_field="clip_embedding", threshold=0.9)
    
    asset = ImageAsset(id="a1", uri="file://1.jpg", name="1", mime_type="image/jpeg", description="", content_hash="h1", clip_embedding=[0.1]*512)
    mock_mapper.vector_search = AsyncMock(return_value=[("a2", 0.95), ("a3", 0.85)])
    
    results = await finder.find_similar(asset)
    
    # Should only return those above threshold (0.9)
    assert len(results) == 1
    assert results[0][0] == "a2"
    assert results[0][1] == 0.95
    
    mock_mapper.vector_search.assert_called_once_with(
        label="ImageAsset",
        property_name="clip_embedding",
        vector=[0.1]*512,
        limit=10
    )
