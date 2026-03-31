"""Async Vector Reduction and Embedding Fusion for BCor Common AI.

This module provides high-level abstractions for managing high-dimensional 
vector data, specifically for multi-model AI systems (e.g., CLIP + BLIP).

Conceptual Overview:
    - Vector Reduction: Projecting high-dim vectors (like 1024D CLIP) into 
      lower-dim space (like 512D) while preserving semantic relationships.
    - PCA vs UMAP: PCA is fast and linear; UMAP is non-linear and preserves 
      complex topological structures but is computationally heavier.
    - Embedding Fusion: Weighted normalization of multiple vector sources 
      into a single, unified "Semantic Fingerprint".

Rationale:
    Heavy ML libraries (sklearn, umap) are imported dynamically to keep the 
    core BCor framework lightweight. All CPU-bound operations are offloaded 
    to thread pools to maintain async responsiveness.

Example:
    >>> reducer = VectorReducer(target_dim=512, method="pca")
    >>> await reducer.fit("clip_model", training_vectors)
    >>> fusion = EmbeddingFusion(reducer=reducer)
    >>> fusion.add_embedding("clip_model", clip_vector, weight=0.7)
    >>> fusion.add_embedding("text_model", text_vector, weight=0.3)
    >>> final_vector = await fusion.fuse()
"""
from __future__ import annotations
import os
import asyncio
import warnings
from typing import Literal, Dict, List, Optional, Any, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    import joblib
    from sklearn.decomposition import PCA, TruncatedSVD
    try:
        import umap
    except ImportError:
        pass

class VectorReducer:
    """Universal class for vector projection using PCA, SVD, or UMAP.
    
    Attributes:
        target_dim: Dimensions to reduce to.
        method: Reduction algorithm ('pca', 'svd', 'umap').
    """

    def __init__(
        self,
        target_dim: int = 512,
        method: Literal["pca", "svd", "umap"] = "svd"
    ):
        self.target_dim = target_dim
        self.method = method
        self.models: Dict[str, Any] = {}

    def _get_joblib(self):
        try:
            import joblib
            return joblib
        except ImportError:
            raise ImportError("joblib is required for VectorReducer. Install with 'uv pip install joblib'")

    def _model_filename(self, name: str) -> str:
        return f"{name}.{self.method}.model"

    async def fit(self, name: str, vectors: np.ndarray) -> None:
        """Fits the reduction model to the provided vectors (Async wrapper)."""
        # Offload heavy CPU work to a thread pool
        await asyncio.to_thread(self._fit_sync, name, vectors)

    def _fit_sync(self, name: str, vectors: np.ndarray) -> None:
        d = min(self.target_dim, vectors.shape[1])

        if self.method == "pca":
            from sklearn.decomposition import PCA
            model = PCA(n_components=d).fit(vectors)
        elif self.method == "svd":
            from sklearn.decomposition import TruncatedSVD
            model = TruncatedSVD(n_components=d).fit(vectors)
        elif self.method == "umap":
            try:
                import umap
            except ImportError:
                raise ImportError("UMAP is not installed. Install with 'uv pip install umap-learn'")
            model = umap.UMAP(n_components=d, random_state=42).fit(vectors)
        else:
            raise ValueError(f"Unknown method: {self.method}")

        self.models[name] = model

    async def transform(self, name: str, vector: np.ndarray) -> np.ndarray:
        """Reduces the dimension of a single vector (Async wrapper)."""
        if name not in self.models:
            raise ValueError(f"Model '{name}' not trained or loaded. Call fit() or load() first.")
        
        # Offload to thread
        return await asyncio.to_thread(self._transform_sync, name, vector)

    def _transform_sync(self, name: str, vector: np.ndarray) -> np.ndarray:
        reduced = self.models[name].transform(vector.reshape(1, -1)).flatten()

        if reduced.shape[0] < self.target_dim:
            padded = np.zeros(self.target_dim, dtype=reduced.dtype)
            padded[:reduced.shape[0]] = reduced
            return padded

        return reduced

    async def save(self, folder: str) -> None:
        """Saves models and metadata to a folder."""
        joblib = self._get_joblib()
        os.makedirs(folder, exist_ok=True)
        meta = {
            "target_dim": self.target_dim,
            "method": self.method,
            "model_names": list(self.models.keys())
        }
        await asyncio.to_thread(joblib.dump, meta, os.path.join(folder, "meta.pkl"))

        for name, model in self.models.items():
            filename = self._model_filename(name)
            await asyncio.to_thread(joblib.dump, model, os.path.join(folder, filename))

    async def load(self, folder: str) -> None:
        """Loads models and metadata from a folder."""
        joblib = self._get_joblib()
        meta_path = os.path.join(folder, "meta.pkl")
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Metadata file missing at {meta_path}")
            
        meta = await asyncio.to_thread(joblib.load, meta_path)
        self.target_dim = meta["target_dim"]
        self.method = meta["method"]
        self.models = {}

        for name in meta["model_names"]:
            filename = self._model_filename(name)
            path = os.path.join(folder, filename)
            if os.path.exists(path):
                self.models[name] = await asyncio.to_thread(joblib.load, path)
            else:
                warnings.warn(f"Model file missing: {filename}")


class EmbeddingFusion:
    """Class for weighted fusion of different embedding types."""

    def __init__(self, reducer: Optional[VectorReducer] = None):
        """Initializes fusion with an optional vector reducer.
        
        If no reducer is provided, embeddings will be fused at their original dimensions
        (must be identical).
        """
        self.reducer = reducer
        self.embeddings: Dict[str, np.ndarray] = {}
        self.weights: Dict[str, float] = {}

    def add_embedding(self, name: str, vector: np.ndarray, weight: float = 1.0) -> None:
        """Adds an embedding to be fused."""
        self.embeddings[name] = vector
        self.weights[name] = weight

    def _normalize(self, v: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(v)
        if norm < 1e-8:
            warnings.warn("Zero-norm vector encountered in EmbeddingFusion.")
            return v
        return v / norm

    async def fuse(self) -> np.ndarray:
        """Fuses all added embeddings into a single normalized vector."""
        total_weight = sum(self.weights.values())
        if total_weight == 0:
            raise ValueError("Total weight must be > 0 in EmbeddingFusion.")

        # Determine target dimension
        target_dim = self.reducer.target_dim if self.reducer else None
        if target_dim is None:
            # Fallback to first embedding dimension if no reducer
            if not self.embeddings:
                raise ValueError("No embeddings added to fuse.")
            target_dim = list(self.embeddings.values())[0].shape[0]

        fused = np.zeros(target_dim, dtype=np.float32)

        for name, vec in self.embeddings.items():
            if self.reducer:
                # Use async transform if reducer is present
                reduced = await self.reducer.transform(name, vec)
            else:
                reduced = vec
                
            normed = self._normalize(reduced)
            fused += self.weights[name] * normed

        fused /= total_weight
        return self._normalize(fused)

    def clear(self) -> None:
        """Clears all added embeddings and weights."""
        self.embeddings.clear()
        self.weights.clear()
