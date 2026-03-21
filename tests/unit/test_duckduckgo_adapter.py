import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.modules.search.adapters.duckduckgo_adapter import DuckDuckGoAdapter

@pytest.mark.asyncio
async def test_duck_duck_go_search_images():
    # Mocking duckduckgo_search.DDGS.images
    mock_results = [
        {
            "title": "Test Image 1",
            "image": "http://example.com/img1.jpg",
            "thumbnail": "http://example.com/thumb1.jpg",
            "url": "http://example.com/page1"
        },
        {
            "title": "Test Image 2",
            "image": "http://example.com/img2.jpg",
            "thumbnail": "http://example.com/thumb2.jpg",
            "url": "http://example.com/page2"
        }
    ]
    
    with patch("src.modules.search.adapters.duckduckgo_adapter.DDGS") as mock_ddgs:
        # DDGS is used as a context manager: with DDGS() as ddgs:
        mock_instance = mock_ddgs.return_value.__enter__.return_value
        mock_instance.images.return_value = mock_results
        
        adapter = DuckDuckGoAdapter()
        results = await adapter.search_images("test query", limit=2)
        
        assert len(results) == 2
        assert results[0].title == "Test Image 1"
        assert results[0].image_url == "http://example.com/img1.jpg"
        assert results[0].source == "DuckDuckGo"
        
        mock_instance.images.assert_called_once_with("test query", max_results=2)
