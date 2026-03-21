"""ImageDedup infrastructure: LLM-based Image Tagger Adapter.
"""
from __future__ import annotations

import re

from loguru import logger

from src.apps.ImageDedup.domain.interfaces.i_image_tagger import IImageTagger
from src.modules.llm.domain.interfaces.llm import ILlmAdapter


class LlmImageTagger(IImageTagger):
    """Image tagger using generic LLM vision capabilities."""

    def __init__(self, llm: ILlmAdapter) -> None:
        self.llm = llm
        self.prompt = (
            "Analyze the attached image and provide tags in the following categories:\n"
            "- General tags (comma separated descriptive tags)\n"
            "- Character names (comma separated, if none say 'none')\n"
            "- Content rating (one of: general, sensitive, questionable, explicit)\n\n"
            "Output format:\n"
            "General: [tags]\n"
            "Characters: [names]\n"
            "Rating: [rating]"
        )

    async def predict_tags(
        self, 
        image_path: str, 
        gen_threshold: float = 0.35, 
        char_threshold: float = 0.75
    ) -> tuple[list[str], list[str], str]:
        """Extract tags using LLM vision."""
        try:
            response = await self.llm.generate_vision_response(self.prompt, image_path)
            logger.debug(f"LLM Tagging response: {response}")
            
            # Simple parsing
            gen_match = re.search(r"General:\s*(.*)", response, re.IGNORECASE)
            char_match = re.search(r"Characters:\s*(.*)", response, re.IGNORECASE)
            rating_match = re.search(r"Rating:\s*(\w+)", response, re.IGNORECASE)
            
            gen_tags = [t.strip() for t in gen_match.group(1).split(",") if t.strip()] if gen_match else []
            char_tags = [
                t.strip() for t in char_match.group(1).split(",") 
                if t.strip() and t.lower() != "none"
            ] if char_match else []
            rating = rating_match.group(1).lower() if rating_match else "unknown"
            
            return gen_tags, char_tags, rating

        except Exception as e:
            logger.error(f"LLM Tagging failed for {image_path}: {e}")
            return [], [], "error"
