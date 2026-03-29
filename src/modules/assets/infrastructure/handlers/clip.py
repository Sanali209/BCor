"""CLIPHandler — Semantic image embeddings using CLIP."""
from __future__ import annotations

import pathlib
from typing import Any

from PIL import Image
from loguru import logger

# Lazy load sentence_transformers to avoid overhead if not used
_model_cache = {}


class CLIPHandler:
    """Handler for computing CLIP embeddings using SentenceTransformers.
    
    Provides 512-dimensional vector embeddings for images.
    """

    @staticmethod
    def _get_model():
        """Lazy loader for the CLIP model."""
        if "clip" not in _model_cache:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("CLIPHandler: Loading clip-ViT-B-32 model...")
                _model_cache["clip"] = SentenceTransformer('clip-ViT-B-32')
            except Exception as e:
                logger.error(f"CLIPHandler: Failed to load model (possibly missing DLLs): {e}")
                return None
        return _model_cache["clip"]

    @staticmethod
    async def run(uri: str, context: dict[str, Any] | None = None) -> list[float]:
        """Compute CLIP embedding for the given image URI.
        
        Args:
            uri: Image file URI.
            context: Optional processing context.
            
        Returns:
            A 512-dimensional list of floats.
        """
        model = CLIPHandler._get_model()
        if not model:
            return []

        from src.core.storage import uri_to_path
        path = uri_to_path(uri)


        if not path.exists():
            logger.warning(f"CLIPHandler: File not found at {path}")
            return []

        try:
            # 1. Open image robustly
            with path.open("rb") as f:
                with Image.open(f) as img:
                    # 2. Encode to vector
                    embedding = model.encode(img)
                    return embedding.astype(float).tolist()
            
        except Exception as e:
            logger.error(f"CLIPHandler failed for {path}: {e}")
            return []
