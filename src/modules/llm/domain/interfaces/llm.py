"""LLM module: updated domain interface with vision support.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ILlmAdapter(Protocol):
    """Port for LLM interactions including vision."""
    
    async def generate_response(self, prompt: str) -> str:
        """Generate a text response for a given prompt."""
        ...

    async def generate_vision_response(self, prompt: str, image_path: str) -> str:
        """Generate a response based on an image and a prompt."""
        ...
