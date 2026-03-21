import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.modules.llm.adapters.gemini_adapter import GeminiAdapter

@pytest.mark.asyncio
async def test_gemini_adapter_generate_response():
    """Test that the adapter calls Gemini and returns the response text."""
    # Mock the google.generativeai module
    with patch("google.generativeai.GenerativeModel") as MockModel:
        # Configure the mock
        mock_model_instance = MagicMock()
        MockModel.return_value = mock_model_instance
        
        # mock_response must have a 'text' attribute
        mock_response = MagicMock()
        mock_response.text = "Hello from AI!"
        
        # generate_content_async should return our mock_response (wrapped for await)
        mock_model_instance.generate_content_async = AsyncMock(return_value=mock_response)
        
        # Instantiate adapter
        adapter = GeminiAdapter(api_key="fake_key", model_name="gemini-test")
        
        # Execute
        response = await adapter.generate_response("Hi!")
        
        # Verify
        assert response == "Hello from AI!"
        mock_model_instance.generate_content_async.assert_called_once_with("Hi!")
        MockModel.assert_called_once_with("gemini-test")
