# DEPRECATED: This module has been modernized and moved to the BCor Common library.
# Please use 'src.common.ai.embeddings' for VectorReducer and EmbeddingFusion.
# The new implementation is async-native and supports VFS.

from src.common.ai.embeddings import VectorReducer, EmbeddingFusion

__all__ = ["VectorReducer", "EmbeddingFusion"]