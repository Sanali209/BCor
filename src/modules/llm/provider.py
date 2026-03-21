"""Dependency injection provider for the LLM module."""
from __future__ import annotations

from dishka import Provider, Scope, provide

from src.modules.llm.adapters.gemini_adapter import GeminiAdapter
from src.modules.llm.domain.interfaces.llm import ILlmAdapter
from src.modules.llm.domain.nlp_pipeline import NlpPipeline


class LlmProvider(Provider):
    """Provider for LLM and NLP related services."""
    
    scope = Scope.REQUEST

    @provide
    def get_llm_adapter(self) -> ILlmAdapter:
        """Provide a Gemini LLM adapter.
        
        Note: In a real system, API key would come from configuration.
        """
        # For now, using a placeholder key. Real migration should use pydantic-settings.
        return GeminiAdapter(api_key="MOCK_API_KEY")

    @provide
    def get_nlp_pipeline(self) -> NlpPipeline:
        """Provide a fresh NLP pipeline instance."""
        return NlpPipeline()
