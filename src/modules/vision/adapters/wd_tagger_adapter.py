"""Vision infrastructure: WD-VIT-Tagger-v3 AI Adapter.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import timm
import torch
from huggingface_hub import hf_hub_download
from loguru import logger
from PIL import Image
from torch import Tensor, nn
from torch.nn import functional as F

from src.modules.vision.domain.interfaces.vision import IVisionTagger


class WDTaggerAdapter(IVisionTagger):
    """Deep-learning based image tagger using WD-VIT-Tagger-v3."""

    def __init__(self, repo_id: str = "SmilingWolf/wd-vit-tagger-v3") -> None:
        self.repo_id = "hf-hub:" + repo_id
        self.raw_repo_id = repo_id
        self.model: nn.Module | None = None
        self.labels: dict[str, Any] | None = None
        self.transform: Any = None
        self.loaded = False
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _load_labels(self) -> dict[str, Any]:
        """Load label data from Hugging Face Hub."""
        csv_path = hf_hub_download(
            repo_id=self.raw_repo_id, filename="selected_tags.csv"
        )
        df = pd.read_csv(csv_path, usecols=["name", "category"])
        return {
            "names": df["name"].tolist(),
            "rating": list(np.where(df["category"] == 9)[0]),
            "general": list(np.where(df["category"] == 0)[0]),
            "character": list(np.where(df["category"] == 4)[0]),
        }

    def _ensure_model_loaded(self) -> None:
        """Lazy-load the model and labels."""
        if self.loaded:
            return

        logger.info(f"Loading WD-Tagger model from {self.repo_id}...")
        self.model = timm.create_model(self.repo_id).eval()
        state_dict = timm.models.load_state_dict_from_hf(self.raw_repo_id)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)

        self.labels = self._load_labels()
        
        # Create transform from model config
        from timm.data import create_transform, resolve_data_config
        config = resolve_data_config(self.model.pretrained_cfg, model=self.model)
        self.transform = create_transform(**config)
        
        self.loaded = True
        logger.info("WD-Tagger model loaded successfully.")

    def _pil_ensure_rgb(self, image: Image.Image) -> Image.Image:
        """Convert image to RGB format, handling transparency."""
        if image.mode not in ["RGB", "RGBA"]:
            image = image.convert("RGBA") if "transparency" in image.info else image.convert("RGB")
        if image.mode == "RGBA":
            canvas = Image.new("RGBA", image.size, (255, 255, 255, 255))
            canvas.alpha_composite(image)
            image = canvas.convert("RGB")
        return image

    def _pil_pad_square(self, image: Image.Image) -> Image.Image:
        """Pad image to square with white background."""
        w, h = image.size
        px = max(image.size)
        canvas = Image.new("RGB", (px, px), (255, 255, 255))
        canvas.paste(image, ((px - w) // 2, (px - h) // 2))
        return canvas

    async def predict_tags(
        self, 
        image_path: str, 
        gen_threshold: float = 0.35, 
        char_threshold: float = 0.75
    ) -> tuple[list[str], list[str], str]:
        """
        Extract tags from image using WD-Tagger.
        """
        try:
            self._ensure_model_loaded()
            if not self.model or not self.labels or not self.transform:
                raise RuntimeError("Model failed to load.")

            # Phase 1: Preprocessing
            with Image.open(image_path) as raw_img:
                img = self._pil_ensure_rgb(raw_img)
                img = self._pil_pad_square(img)
                
                # Phase 2: Inference
                input_tensor: Tensor = self.transform(img).unsqueeze(0)
                # RGB to BGR as expected by the model
                input_tensor = input_tensor[:, [2, 1, 0]].to(self.device)

                with torch.inference_mode():
                    outputs = self.model.forward(input_tensor)
                    probs = F.sigmoid(outputs).squeeze(0).cpu().numpy()

            # Phase 3: Post-processing
            names = self.labels["names"]
            
            # Rating
            rating_probs = {names[i]: probs[i] for i in self.labels["rating"]}
            rating = max(rating_probs.items(), key=lambda x: x[1])[0] if rating_probs else "unknown"

            # General tags
            gen_tags = [
                names[i] for i in self.labels["general"] 
                if probs[i] > gen_threshold
            ]
            gen_tags.sort(key=lambda x: probs[names.index(x)], reverse=True)

            # Character tags
            char_tags = [
                names[i] for i in self.labels["character"] 
                if probs[i] > char_threshold
            ]
            char_tags.sort(key=lambda x: probs[names.index(x)], reverse=True)

            return gen_tags, char_tags, str(rating)

        except Exception as e:
            logger.error(f"Failed to predict tags for {image_path}: {e}")
            return [], [], "error"
