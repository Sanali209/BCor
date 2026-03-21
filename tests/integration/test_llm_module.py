import pytest
from unittest.mock import AsyncMock, patch

from dishka import Provider, Scope, provide, make_async_container
from bubus import EventBus

from src.modules.llm.domain.interfaces.llm import ILlmAdapter
from src.modules.llm.domain.nlp_pipeline import NlpPipeline
from src.modules.llm.messages import ProcessTextCommand, TextProcessedEvent, ResponseGeneratedEvent
from src.modules.llm.handlers import handle_process_text

class LlmTestProvider(Provider):
    """Provider to inject mocks specifically for testing.
    
    Renamed from TestLlmProvider to avoid PytestCollectionWarning.
    """
    scope = Scope.REQUEST

    @provide
    def get_llm_adapter(self) -> ILlmAdapter:
        mock = AsyncMock(spec=ILlmAdapter)
        mock.generate_response.return_value = "Mocked LLM Response"
        return mock

    @provide
    def get_nlp_pipeline(self) -> NlpPipeline:
        return NlpPipeline()

@pytest.mark.asyncio
async def test_llm_module_flow():
    """Integration test for the full LLM/NLP flow using Dishka and EventBus."""
    with patch("src.modules.llm.domain.nlp_pipeline.nltk") as mock_nltk:
        # Mock tokenization
        mock_nltk.word_tokenize.side_effect = lambda x: x.lower().split()
        
        # 1. Setup Container with Test Provider
        container = make_async_container(LlmTestProvider())
        
        # 2. Setup Bus (provided by bubus)
        bus = EventBus()
        
        # 3. Capture Events
        events = []
        # Use .on() for bubus subscription
        bus.on(TextProcessedEvent, lambda e: events.append(e))
        bus.on(ResponseGeneratedEvent, lambda e: events.append(e))

        async def run_with_container(cmd):
            async with container() as request_container:
                # Resolve dependencies
                nlp = await request_container.get(NlpPipeline)
                llm = await request_container.get(ILlmAdapter)
                # Dispatch command simulation (manually calling handler for local test)
                await handle_process_text(cmd, nlp, llm, bus)

        # 4. Execute Command
        cmd = ProcessTextCommand(
            text="Geralt of Rivia is a witcher.",
            use_nlp=True,
            prompt_template="Summarize this: {text}"
        )
        
        # Setup一些规则
        async with container() as req:
            nlp = await req.get(NlpPipeline)
            nlp.add_extend_rule(",tag|", ["geralt of rivia"])
        
        await run_with_container(cmd)

        # 5. Assertions
        assert len(events) == 2
        
        processed_ev = next(e for e in events if isinstance(e, TextProcessedEvent))
        assert processed_ev.original_text == "Geralt of Rivia is a witcher."
        
        response_ev = next(e for e in events if isinstance(e, ResponseGeneratedEvent))
        assert response_ev.response == "Mocked LLM Response"
