"""BLIPHandler — Semantic image embeddings using BLIP."""
from __future__ import annotations

import pathlib
from typing import Any


from PIL import Image
from loguru import logger

# Lazy load transformers to avoid overhead if not used
_model_cache = {}


class BLIPHandler:
    """Handler for computing BLIP embeddings using Transformers.
    
    Provides 768-dimensional vector embeddings for images.
    """

    @classmethod
    def _get_model(cls):
        """Lazy loader for BLIP model and processor."""
        if "blip" not in _model_cache:
            try:
                from transformers import BlipProcessor, BlipForConditionalGeneration
                logger.info("BLIPHandler: Loading Salesforce/blip-image-captioning-base (multimodal)...")
                _model_cache["processor"] = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
                _model_cache["blip"] = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            except Exception as e:
                logger.error(f"BLIPHandler: Failed to load transformers/torch: {e}")
                return None, None
        return _model_cache["processor"], _model_cache["blip"]

    @classmethod
    async def run(cls, uri: str, context: dict[str, Any] | None = None) -> list[float]:
        """Compute BLIP embedding for the given image URI.
        
        Args:
            uri: Image file URI.
            context: Optional processing context.
            
        Returns:
            A 768-dimensional list of floats.
        """
        processor, model = cls._get_model()
        if not model or not processor:
            return "" if "caption" in (context or {}).get("handler", "") else []

        from src.core.storage import uri_to_path
        path = uri_to_path(uri)

        if not path.exists():
            logger.warning(f"BLIPHandler: File not found at {path}")
            return "" if "caption" in (context or {}).get("handler", "") else []

        try:
            # 1. Open image robustly
            with path.open("rb") as f:
                with Image.open(f) as img:
                    import torch
                    handler_name = context.get("handler", "") if context else ""
                    is_caption = "caption" in handler_name or "caption" in (context or {}).get("field_name", "")

                    inputs = processor(images=img, return_tensors="pt")
                    with torch.no_grad():
                        if is_caption:
                            # Generate Caption
                            generated_ids = model.generate(**inputs, max_new_tokens=40)
                            caption = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                            logger.debug(f"BLIPHandler: Generated caption: {caption}")
                            return str(caption)
                        
                        # Extract Embeddings (ViT-B-32 base vision model)
                        # We use vision_model hidden state (features)
                        # The vision_model returns BaseModelOutputWithPooling
                        vision_outputs = model.vision_model(**inputs)
                        
                        # Normalized vector (BLIP-base vision features are 768)
                        # The vision transformer output is (batch, 577, 768)
                        # We use the [CLS] token at index 0.
                        last_hidden_state = vision_outputs.last_hidden_state
                        pooled = last_hidden_state[:, 0, :]  # Shape (1, 768)
                        
                        # Convert to list of floats
                        result = pooled.squeeze().detach().cpu().numpy().astype(float).tolist()
                        
                        if len(result) != 768:
                             logger.warning(f"BLIPHandler: Unexpected vector size {len(result)}. Attempting resize.")
                             import numpy as np
                             result = result[:768] if len(result) > 768 else (result + [0.0] * (768 - len(result)))

                        return result
            
        except Exception as e:
            logger.error(f"BLIPHandler failed for {path}: {e}")
            return []
