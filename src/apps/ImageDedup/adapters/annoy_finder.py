from __future__ import annotations

from typing import Any, cast

import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from annoy import AnnoyIndex
from loguru import logger
from PIL import Image

from src.apps.ImageDedup.domain.interfaces.i_image_differ import IDuplicateFinder


class AnnoyDuplicateFinder(IDuplicateFinder):
    """Deep-learning based duplicate finder using CNN features and Annoy."""

    def __init__(self, vector_size: int = 576, resize_dim: tuple[int, int] = (720, 720)) -> None:
        self.vector_size = vector_size
        self._index: AnnoyIndex | None = None
        self._paths: list[str] = []
        
        # Initialize model (MobileNetV3 Small)
        # We strip the classification head to get the feature vector
        base_model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
        self.model = nn.Sequential(*list(base_model.children())[:-1])
        self.model.eval()
        
        self.preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])

    def _get_embedding(self, path: str) -> np.ndarray[Any, np.dtype[np.float32]]:
        """Computes the CNN embedding for an image."""
        try:
            with Image.open(path) as img_raw:
                img = img_raw.convert('RGB')
                tensor = self.preprocess(img).unsqueeze(0)
                with torch.no_grad():
                    features = self.model(tensor)
                    return cast(np.ndarray[Any, np.dtype[np.float32]], features.squeeze().numpy().flatten())
        except Exception as e:
            logger.error(f"Failed to embed image {path}: {e}")
            return np.zeros(self.vector_size, dtype=np.float32)

    def build_index(self, file_paths: list[str]) -> None:
        """Indexes all provided images."""
        self._paths = file_paths
        self._index = AnnoyIndex(self.vector_size, 'euclidean')
        
        logger.info(f"Building Annoy index for {len(file_paths)} images...")
        for i, path in enumerate(file_paths):
            embedding = self._get_embedding(path)
            self._index.add_item(i, embedding)
            
        self._index.build(10) # 10 trees
        logger.info("Annoy index built successfully.")

    def find_duplicates(
        self, 
        similarity_threshold: float = 0.95
    ) -> dict[str, list[str]]:
        """Finds duplicates based on distance threshold.
        
        Note: similarity_threshold 0.95 -> distance threshold 
        (Implementation detail: we use a heuristic mapping from similarity to euclidean distance).
        """
        if not self._index:
            return {}

        duplicates = {}
        processed = set()
        
        # Mapping 0.95 similarity to a small distance threshold
        # (In Euclidean space, 0 distance = exact match)
        dist_threshold = (1.0 - similarity_threshold) * 10.0 # Simple heuristic

        for i in range(len(self._paths)):
            if i in processed:
                continue
                
            # Find nearest neighbors
            neighbors, distances = self._index.get_nns_by_item(i, 10, include_distances=True)
            
            group = []
            for neighbor_idx, dist in zip(neighbors, distances, strict=True):
                if neighbor_idx == i:
                    continue
                if dist < dist_threshold:
                    group.append(self._paths[neighbor_idx])
                    processed.add(neighbor_idx)
            
            if group:
                duplicates[self._paths[i]] = group
                
        return duplicates

    def get_thumbnail(self, path: str, max_size: tuple[int, int] | None = None) -> Image.Image:
        """Generates a thumbnail for a given image path."""
        try:
            with Image.open(path) as img:
                img.thumbnail(max_size or (128, 128))
                return img
        except Exception as e:
            logger.error(f"Failed to generate thumbnail for {path}: {e}")
            # Return a blank image or raise an error, depending on desired behavior
            return Image.new('RGB', max_size or (128, 128), color = 'red')

    def find_top_similar(self, path: str, top_k: int = 6) -> list[str]:
        """Finds top K similar images to a given path (even if not in index)."""
        embedding = self._get_embedding(path)
        if not self._index:
            return []
            
        neighbors = self._index.get_nns_by_vector(embedding, top_k + 1)
        # Filter out the image itself if it's in the index
        results = [self._paths[n] for n in neighbors if self._paths[n] != path]
        return results[:top_k]
