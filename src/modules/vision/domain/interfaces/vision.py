"""Vision infrastructure: Domain interfaces.
"""
from __future__ import annotations

import abc


class IVisionTagger(abc.ABC):
    """Port: generic image tagging functionality."""

    @abc.abstractmethod
    async def predict_tags(
        self, 
        image_path: str, 
        gen_threshold: float = 0.35, 
        char_threshold: float = 0.75
    ) -> tuple[list[str], list[str], str]:
        """
        Extract tags and rating from an image.
        
        Returns:
            Tuple of (general_tags, character_tags, rating)
        """
        raise NotImplementedError
