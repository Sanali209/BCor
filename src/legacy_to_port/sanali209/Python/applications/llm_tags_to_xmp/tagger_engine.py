"""
LLM Tagger Engine - SmilingWolfTagger Integration
Extracts tags, characters, and ratings from images using the WD-VIT-Tagger-v3 model
"""
import sys
import os

# Add Python directory to path to access SLM framework
python_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)

import torch
from torch import Tensor, nn
from torch.nn import functional as F
import timm
from timm.data import create_transform, resolve_data_config
from PIL import Image
import numpy as np
import pandas as pd
from huggingface_hub import hf_hub_download
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Import comprehensive logging
from SLM.logging import (
    image_logger,
    ProcessingPhase,
    LogLevel,
    get_image_context,
    log_image_validation
)


torch_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


@dataclass
class LabelData:
    names: list[str]
    rating: list[np.int64]
    general: list[np.int64]
    character: list[np.int64]


def pil_ensure_rgb(image: Image.Image) -> Image.Image:
    """Convert image to RGB format"""
    if image.mode not in ["RGB", "RGBA"]:
        image = image.convert("RGBA") if "transparency" in image.info else image.convert("RGB")
    if image.mode == "RGBA":
        canvas = Image.new("RGBA", image.size, (255, 255, 255))
        canvas.alpha_composite(image)
        image = canvas.convert("RGB")
    return image


def pil_pad_square(image: Image.Image) -> Image.Image:
    """Pad image to square with white background"""
    w, h = image.size
    px = max(image.size)
    canvas = Image.new("RGB", (px, px), (255, 255, 255))
    canvas.paste(image, ((px - w) // 2, (px - h) // 2))
    return canvas


def load_labels_hf(
    repo_id: str,
    revision: Optional[str] = None,
    token: Optional[str] = None,
) -> LabelData:
    """Load label data from Hugging Face Hub"""
    csv_path = hf_hub_download(
        repo_id=repo_id, filename="selected_tags.csv", revision=revision, token=token
    )
    csv_path = Path(csv_path).resolve()
    
    df: pd.DataFrame = pd.read_csv(csv_path, usecols=["name", "category"])
    tag_data = LabelData(
        names=df["name"].tolist(),
        rating=list(np.where(df["category"] == 9)[0]),
        general=list(np.where(df["category"] == 0)[0]),
        character=list(np.where(df["category"] == 4)[0]),
    )
    
    return tag_data


def get_tags(
    probs: Tensor,
    labels: LabelData,
    gen_threshold: float,
    char_threshold: float,
):
    """Extract tags from model predictions"""
    probs = list(zip(labels.names, probs.numpy()))
    
    # Rating labels
    rating_labels = dict([probs[i] for i in labels.rating])
    
    # General labels
    gen_labels = [probs[i] for i in labels.general]
    gen_labels = dict([x for x in gen_labels if x[1] > gen_threshold])
    gen_labels = dict(sorted(gen_labels.items(), key=lambda item: item[1], reverse=True))
    
    # Character labels
    char_labels = [probs[i] for i in labels.character]
    char_labels = dict([x for x in char_labels if x[1] > char_threshold])
    char_labels = dict(sorted(char_labels.items(), key=lambda item: item[1], reverse=True))
    
    return rating_labels, char_labels, gen_labels


class TaggerEngine:
    """SmilingWolf WD-VIT-Tagger-v3 Engine"""
    
    def __init__(self):
        self.repo_id = "SmilingWolf/wd-vit-tagger-v3"
        self.model: nn.Module = None
        self.labels: LabelData = None
        self.transform = None
        self.loaded = False
        
    def load_model(self):
        """Load the model and labels"""
        if self.loaded:
            return
        
        # Load model
        self.model = timm.create_model("hf-hub:" + self.repo_id).eval()
        state_dict = timm.models.load_state_dict_from_hf(self.repo_id)
        self.model.load_state_dict(state_dict)
        
        # Load labels
        self.labels = load_labels_hf(self.repo_id)
        
        # Create transform
        self.transform = create_transform(**resolve_data_config(self.model.pretrained_cfg, model=self.model))
        
        self.loaded = True
    
    def get_best_rating(self, ratings: dict[str, float]) -> str:
        """Get rating with highest confidence"""
        if not ratings:
            return None
        return max(ratings.items(), key=lambda x: x[1])[0]
    
    def predict(self, image_path: str, gen_threshold: float = 0.35, char_threshold: float = 0.75, batch_id: str = None):
        """
        Predict tags for an image with comprehensive logging

        Returns:
            tuple: (general_tags, character_tags, rating)
        """
        # Create image context for logging
        image_context = get_image_context(image_path, batch_id,
                                        gen_threshold=gen_threshold,
                                        char_threshold=char_threshold)

        with image_logger.operation_context(ProcessingPhase.INFERENCE, "tag_prediction", image_context):
            if not self.loaded:
                with image_logger.operation_context(ProcessingPhase.PREPROCESSING, "model_loading", image_context):
                    self.load_model()
                    image_logger.log_event(
                        ProcessingPhase.PREPROCESSING,
                        LogLevel.INFO,
                        image_context,
                        "model_loaded",
                        f"Model loaded successfully for {image_context.filename}"
                    )

            # Phase 1: Image Loading and Validation
            with image_logger.operation_context(ProcessingPhase.VALIDATION, "image_loading", image_context):
                try:
                    img_input = Image.open(image_path)
                    original_size = img_input.size
                    original_mode = img_input.mode

                    # Validate image can be processed
                    if img_input.size[0] == 0 or img_input.size[1] == 0:
                        raise ValueError(f"Invalid image dimensions: {img_input.size}")

                    log_image_validation(image_path, True, batch_id=batch_id)

                except Exception as e:
                    log_image_validation(image_path, False, [str(e)], batch_id=batch_id)
                    raise

            # Phase 2: Image Preprocessing
            with image_logger.operation_context(ProcessingPhase.PREPROCESSING, "image_preprocessing", image_context):
                img_input = pil_ensure_rgb(img_input)
                img_input = pil_pad_square(img_input)

                preprocessing_metrics = {
                    'original_size': original_size,
                    'original_mode': original_mode,
                    'processed_size': img_input.size,
                    'processed_mode': img_input.mode
                }

                image_logger.log_event(
                    ProcessingPhase.PREPROCESSING,
                    LogLevel.DEBUG,
                    image_context,
                    "preprocessing_complete",
                    f"Image preprocessing completed: {original_size} -> {img_input.size}",
                    performance_metrics=preprocessing_metrics
                )

            # Phase 3: Tensor Transformation
            with image_logger.operation_context(ProcessingPhase.PREPROCESSING, "tensor_transform", image_context):
                inputs: Tensor = self.transform(img_input).unsqueeze(0)
                # RGB to BGR conversion for model
                inputs = inputs[:, [2, 1, 0]]

                tensor_metrics = {
                    'tensor_shape': list(inputs.shape),
                    'tensor_dtype': str(inputs.dtype),
                    'device': str(torch_device)
                }

            # Phase 4: Model Inference
            with image_logger.operation_context(ProcessingPhase.INFERENCE, "model_inference", image_context):
                inference_start = torch.cuda.Event(enable_timing=True) if torch_device.type != "cpu" else None
                inference_end = torch.cuda.Event(enable_timing=True) if torch_device.type != "cpu" else None

                if torch_device.type != "cpu":
                    if inference_start:
                        inference_start.record()
                    model = self.model.to(torch_device)
                    inputs = inputs.to(torch_device)

                with torch.inference_mode():
                    outputs = model.forward(inputs)
                    outputs = F.sigmoid(outputs)

                if torch_device.type != "cpu":
                    if inference_end:
                        inference_end.record()
                        torch.cuda.synchronize()
                        inference_time = inference_start.elapsed_time(inference_end) if inference_start and inference_end else 0
                    else:
                        inference_time = 0

                    inputs = inputs.to("cpu")
                    outputs = outputs.to("cpu")
                    model = model.to("cpu")
                else:
                    inference_time = 0

                inference_metrics = {
                    'output_shape': list(outputs.shape),
                    'inference_device': str(torch_device),
                    'inference_time_ms': inference_time,
                    'batch_size': inputs.shape[0]
                }

                image_logger.log_event(
                    ProcessingPhase.INFERENCE,
                    LogLevel.DEBUG,
                    image_context,
                    "inference_complete",
                    f"Model inference completed in {inference_time:.2f}ms",
                    performance_metrics=inference_metrics
                )

            # Phase 5: Tag Extraction and Post-processing
            with image_logger.operation_context(ProcessingPhase.POST_PROCESSING, "tag_extraction", image_context):
                rating_labels, char_labels, gen_labels = get_tags(
                    probs=outputs.squeeze(0),
                    labels=self.labels,
                    gen_threshold=gen_threshold,
                    char_threshold=char_threshold,
                )

                # Format output
                general_tags = list(gen_labels.keys())
                character_tags = list(char_labels.keys())
                rating = self.get_best_rating(rating_labels)

                postprocessing_metrics = {
                    'general_tags_count': len(general_tags),
                    'character_tags_count': len(character_tags),
                    'rating': rating,
                    'gen_threshold': gen_threshold,
                    'char_threshold': char_threshold,
                    'top_general_confidence': max(gen_labels.values()) if gen_labels else 0,
                    'top_character_confidence': max(char_labels.values()) if char_labels else 0
                }

                image_logger.log_event(
                    ProcessingPhase.POST_PROCESSING,
                    LogLevel.INFO,
                    image_context,
                    "tag_extraction_complete",
                    f"Extracted {len(general_tags)} general, {len(character_tags)} character tags, rating: {rating}",
                    performance_metrics=postprocessing_metrics
                )

            return general_tags, character_tags, rating
