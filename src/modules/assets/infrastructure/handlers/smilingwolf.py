"""SmilingWolfHandler - Image auto-tagging using timm and wd-v3 models."""
from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import pandas as pd
import torch
from loguru import logger
from PIL import Image
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import HfHubHTTPError

from src.modules.assets.domain.models import Tag

_model_cache = {}

MODEL_REPO = "SmilingWolf/wd-vit-tagger-v3"
torch_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


@dataclass
class LabelData:
    names: list[str]
    rating: list[np.int64]
    general: list[np.int64]
    character: list[np.int64]


def pil_ensure_rgb(image: Image.Image) -> Image.Image:
    if image.mode not in ["RGB", "RGBA"]:
        image = image.convert("RGBA") if "transparency" in image.info else image.convert("RGB")
    if image.mode == "RGBA":
        canvas = Image.new("RGBA", image.size, (255, 255, 255))
        canvas.alpha_composite(image)
        image = canvas.convert("RGB")
    return image


def pil_pad_square(image: Image.Image) -> Image.Image:
    w, h = image.size
    px = max(image.size)
    canvas = Image.new("RGB", (px, px), (255, 255, 255))
    canvas.paste(image, ((px - w) // 2, (px - h) // 2))
    return canvas


def load_labels_hf(repo_id: str, revision: Optional[str] = None, token: Optional[str] = None) -> LabelData:
    try:
        csv_path = hf_hub_download(repo_id=repo_id, filename="selected_tags.csv", revision=revision, token=token)
        csv_path = pathlib.Path(csv_path).resolve()
    except HfHubHTTPError as e:
        raise FileNotFoundError(f"selected_tags.csv failed to download from {repo_id}") from e

    df: pd.DataFrame = pd.read_csv(csv_path, usecols=["name", "category"])
    return LabelData(
        names=df["name"].tolist(),
        rating=list(np.where(df["category"] == 9)[0]),
        general=list(np.where(df["category"] == 0)[0]),
        character=list(np.where(df["category"] == 4)[0]),
    )


def get_tags(probs: torch.Tensor, labels: LabelData, gen_threshold: float, char_threshold: float):
    probs_mapped = list(zip(labels.names, probs.numpy()))
    
    rating_labels = dict([probs_mapped[i] for i in labels.rating])
    
    gen_labels = [probs_mapped[i] for i in labels.general]
    gen_labels = {name: prob for name, prob in gen_labels if prob > gen_threshold}
    gen_labels = dict(sorted(gen_labels.items(), key=lambda item: item[1], reverse=True))

    char_labels = [probs_mapped[i] for i in labels.character]
    char_labels = {name: prob for name, prob in char_labels if prob > char_threshold}
    char_labels = dict(sorted(char_labels.items(), key=lambda item: item[1], reverse=True))

    combined_names = list(gen_labels.keys()) + list(char_labels.keys())
    taglist = ", ".join(combined_names).replace("_", " ")
    
    return taglist, rating_labels, char_labels, gen_labels


def get_best_rating(ratings: dict[str, float]) -> str | None:
    best_rating = None
    max_val = -1.0
    for key, value in ratings.items():
        if value > max_val:
            max_val = value
            best_rating = key
    return best_rating


class SmilingWolfHandler:
    """Graph-native Semantic image tagging using SmilingWolf/wd-vit-tagger-v3.
    
    Returns a list of `Tag` dataclasses adapted for the graph `HAS_TAG` relation.
    """
    
    @classmethod
    def _get_model(cls):
        if "sw_model" not in _model_cache:
            import timm
            logger.info(f"SmilingWolfHandler: Loading {MODEL_REPO}...")
            
            try:
                model = timm.create_model("hf-hub:" + MODEL_REPO).eval()
                state_dict = timm.models.load_state_dict_from_hf(MODEL_REPO)
                model.load_state_dict(state_dict)
                labels = load_labels_hf(MODEL_REPO)
                transform = timm.data.create_transform(**timm.data.resolve_data_config(model.pretrained_cfg, model=model))
                
                _model_cache["sw_model"] = model
                _model_cache["sw_labels"] = labels
                _model_cache["sw_transform"] = transform
            except Exception as e:
                logger.error(f"SmilingWolfHandler: Failed to load timm model: {e}")
                return None, None, None

        return _model_cache["sw_model"], _model_cache["sw_labels"], _model_cache["sw_transform"]

    @classmethod
    async def run(cls, uri: str, context: dict[str, Any] | None = None) -> list[Tag]:
        """Process an image and output hierarchical graph Tag objects."""
        model, labels, transform = cls._get_model()
        if not model or not labels or not transform:
            return []
            
        from src.core.storage import uri_to_path
        path = uri_to_path(uri)


        if not path.exists():
            logger.warning(f"SmilingWolfHandler: File not found at {path}")
            return []

        try:
            with path.open("rb") as f:
                with Image.open(f) as img:
                    img_rgb = pil_ensure_rgb(img)
                    img_padded = pil_pad_square(img_rgb)
                    
            inputs = transform(img_padded).unsqueeze(0)
            # NCHW image RGB to BGR
            inputs = inputs[:, [2, 1, 0]]
            
            from torch.nn import functional as F
            
            with torch.inference_mode():
                if torch_device.type != "cpu":
                    model = model.to(torch_device)
                    inputs = inputs.to(torch_device)
                
                outputs = model.forward(inputs)
                outputs = F.sigmoid(outputs)
                
                if torch_device.type != "cpu":
                    outputs = outputs.to("cpu")

            _, ratings, char_labels, gen_labels = get_tags(
                probs=outputs.squeeze(0),
                labels=labels,
                gen_threshold=0.35,
                char_threshold=0.75,
            )

            # Build list of Tag graph nodes
            tags = []
            
            import uuid
            # 1. General tags
            for label in gen_labels.keys():
                name = f"auto/wd_tag/{label.strip()}"
                tags.append(Tag(id=name, name=name))
                
            # 2. Characters
            for char_label in char_labels.keys():
                name = f"auto/wd_character/{char_label.strip()}"
                tags.append(Tag(id=name, name=name))
                
            # 3. Best Rating
            best_rating = get_best_rating(ratings)
            if best_rating:
                name = f"auto/wd_rating/{str(best_rating)}"
                tags.append(Tag(id=name, name=name))

            logger.info(f"SmilingWolfHandler: Extracted {len(tags)} tags for {path.name}")
            return tags

        except Exception as e:
            logger.error(f"SmilingWolfHandler failed for {path}: {e}")
            return []
