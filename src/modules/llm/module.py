"""LLM Module definition for the BCor system."""
from __future__ import annotations

from typing import Any

from collections.abc import Iterable

from dishka import Provider

from src.core.module import BaseModule
from src.modules.llm.handlers import handle_generate_response, handle_process_text
from src.modules.llm.messages import GenerateResponseCommand, ProcessTextCommand
from src.modules.llm.provider import LlmProvider


class LlmModule(BaseModule):
    """Module for LLM and NLP processing."""

    def get_providers(self) -> Iterable[Provider]:
        """Return the module's dependency providers."""
        return [LlmProvider()]

    def register_handlers(self, bus: Any) -> None:
        """Register command handlers with the message bus."""
        bus.subscribe(GenerateResponseCommand, handle_generate_response)
        bus.subscribe(ProcessTextCommand, handle_process_text)
