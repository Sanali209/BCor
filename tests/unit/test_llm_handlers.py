import pytest
from unittest.mock import AsyncMock, MagicMock
from bubus import EventBus

from src.modules.llm.handlers import handle_generate_response, handle_process_text
from src.modules.llm.messages import (
    GenerateResponseCommand,
    ProcessTextCommand,
    ResponseGeneratedEvent,
    TextProcessedEvent,
)
from src.modules.llm.domain.interfaces.llm import ILlmAdapter
from src.modules.llm.domain.nlp_pipeline import NlpPipeline

@pytest.mark.asyncio
async def test_handle_generate_response():
    # Setup
    mock_llm = AsyncMock(spec=ILlmAdapter)
    mock_llm.generate_response.return_value = "Test response"
    
    mock_bus = AsyncMock(spec=EventBus)
    mock_bus.dispatch = AsyncMock()
    
    cmd = GenerateResponseCommand(prompt="Test prompt")
    
    # Execute
    await handle_generate_response(cmd, mock_llm, mock_bus)
    
    # Assert
    mock_llm.generate_response.assert_called_once_with("Test prompt")
    mock_bus.dispatch.assert_called_once()
    event = mock_bus.dispatch.call_args[0][0]
    assert isinstance(event, ResponseGeneratedEvent)
    assert event.response == "Test response"

@pytest.mark.asyncio
async def test_handle_process_text():
    # Setup
    mock_llm = AsyncMock(spec=ILlmAdapter)
    mock_llm.generate_response.return_value = "LLM Answer"
    
    mock_nlp = MagicMock(spec=NlpPipeline)
    mock_nlp.get_text.return_value = "Processed Text"
    mock_nlp.get_tokens.return_value = ["token1"]
    
    mock_bus = AsyncMock(spec=EventBus)
    mock_bus.dispatch = AsyncMock()
    
    cmd = ProcessTextCommand(
        text="Original Text",
        use_nlp=True,
        prompt_template="Prompt: {text}"
    )
    
    # Execute
    await handle_process_text(cmd, mock_nlp, mock_llm, mock_bus)
    
    # Assert
    mock_nlp.set_text.assert_called_once_with("Original Text")
    mock_nlp.run.assert_called_once()
    mock_llm.generate_response.assert_called_once_with("Prompt: Processed Text")
    
    assert mock_bus.dispatch.call_count == 2
    events = [call[0][0] for call in mock_bus.dispatch.call_args_list]
    
    text_processed_ev = next(e for e in events if isinstance(e, TextProcessedEvent))
    assert text_processed_ev.processed_text == "Processed Text"
    
    response_ev = next(e for e in events if isinstance(e, ResponseGeneratedEvent))
    assert response_ev.response == "LLM Answer"
