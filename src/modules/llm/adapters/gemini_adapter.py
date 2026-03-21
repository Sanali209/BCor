"""Gemini LLM Adapter implementation.

Ported from legacy SLM/LangChain/LangChainHelper.py.
"""
from __future__ import annotations

import google.generativeai as genai

from src.modules.llm.domain.interfaces.llm import ILlmAdapter


class GeminiAdapter(ILlmAdapter):
    """Adapter for Google Gemini API."""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash") -> None:
        """Initialize the adapter.
        
        Args:
            api_key: The Google AI Studio API key.
            model_name: The name of the Gemini model to use.
        """
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=self.api_key)  # type: ignore[attr-defined]
        self.model = genai.GenerativeModel(self.model_name)  # type: ignore[attr-defined]

    async def generate_response(self, prompt: str) -> str:
        """Generate a response for a given prompt."""
        try:
            response = await self.model.generate_content_async(prompt)
            return str(response.text)
        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {e}") from e

    async def generate_vision_response(self, prompt: str, image_path: str) -> str:
        """Generate a response based on an image and a prompt."""
        try:
            # Load image using PIL for Gemini SDK
            import PIL.Image
            img = PIL.Image.open(image_path)
            
            response = await self.model.generate_content_async([prompt, img])
            return str(response.text)
        except Exception as e:
            raise RuntimeError(f"Gemini Vision API call failed: {e}") from e
