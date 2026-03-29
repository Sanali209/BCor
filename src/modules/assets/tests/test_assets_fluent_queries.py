import pytest
from unittest.mock import AsyncMock, MagicMock
from src.modules.assets.infrastructure.search import SearchService, SearchQuery
from src.modules.assets.infrastructure.dedup import SemanticDuplicateFinder
from src.modules.assets.domain.models import ImageAsset

@pytest.fixture
def mapper():
    m = MagicMock()
    # Mock the query() method returning a CypherQuery mock
    q = MagicMock()
    q.where.return_value = q
    q.limit.return_value = q
    q.skip.return_value = q
    q.fetch = AsyncMock(return_value=[])
    m.query.return_value = q
    return m

@pytest.mark.asyncio
async def test_search_service_fluent_call(mapper):
    service = SearchService(mapper)
    query = SearchQuery(text="cat", mime_filter="image/*", limit=10)
    session = AsyncMock()
    
    await service.search(query, session=session)
    
    # Verify that mapper.query was called with Asset (base class)
    from src.modules.assets.domain.models import Asset
    mapper.query.assert_called_once_with(Asset, session=session)
    
    # Verify chain
    q_mock = mapper.query.return_value
    assert q_mock.where.call_count >= 2 # one for text, one for mime
    q_mock.limit.assert_called_with(10)
    q_mock.fetch.assert_called_once()

@pytest.mark.asyncio
async def test_dedup_service_fluent_call(mapper):
    finder = SemanticDuplicateFinder(mapper=mapper)
    asset = ImageAsset(id="a1", name="cat", uri="file://1.jpg", mime_type="image/jpeg")
    asset.embedding = [0.1] * 384
    session = AsyncMock()
    
    await finder.find_similar_in_db(asset, session=session)
    
    from src.modules.assets.domain.models import Asset
    mapper.query.assert_called_once_with(Asset, session=session)
    
    q_mock = mapper.query.return_value
    q_mock.where.assert_called() # excluding self
    q_mock.fetch.assert_called_once()
