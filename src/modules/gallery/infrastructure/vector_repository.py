from typing import Dict, List, Any, Optional
from uuid import UUID

from ..domain.interfaces import VectorSearchProvider
from .chroma_adapter import ChromaAdapter

class ChromaVectorRepository(VectorSearchProvider):
    """Implementation of VectorSearchProvider using ChromaDB."""

    def __init__(self, adapter: ChromaAdapter, default_model: str = "clip") -> None:
        self.adapter = adapter
        self.default_model = default_model

    def _get_collection_name(self, model: str) -> str:
        return f"gallery_{model}"

    def search_similar_text(self, text: str, model: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for images similar to text descripton.
        Note: This requires the text to be embedded first by an external AI service.
        In this Clean Architecture, the Application layer handles the embedding.
        """
        # This is a placeholder for the logic that will be called from search use cases
        # The query vector will be passed in as 'text' if it's already embedded, 
        # or we might need a separate method for 'search_by_vector'.
        return []

    def search_similar_image(self, image_id: UUID, model: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Find images similar to the one identified by image_id."""
        collection_name = self._get_collection_name(model)
        # 1. Get embedding of the source image
        results = self.adapter.get_by_ids(collection_name, [str(image_id)])
        
        if not results or not results['embeddings'] or len(results['embeddings']) == 0:
            return []
            
        source_embedding = results['embeddings'][0]
        
        # 2. Query for similar images
        query_results = self.adapter.query_similar(
            collection_name=collection_name,
            query_embeddings=[source_embedding],
            n_results=limit
        )
        
        return self._format_results(query_results)

    def add_vector(self, image_id: UUID, vector: List[float], model: str, metadata: Dict[str, Any]) -> None:
        collection_name = self._get_collection_name(model)
        self.adapter.add_vectors(
            collection_name=collection_name,
            ids=[str(image_id)],
            embeddings=[vector],
            metadatas=[metadata]
        )

    def _format_results(self, query_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format Chroma query results into a standardized list of dicts."""
        formatted = []
        if not query_results['ids'] or len(query_results['ids']) == 0:
            return []
            
        ids = query_results['ids'][0]
        distances = query_results['distances'][0]
        metadatas = query_results['metadatas'][0] if query_results['metadatas'] else [None] * len(ids)
        
        for i in range(len(ids)):
            # Convert distance to similarity score (cosine similarity implementation assumes distance is 1-cos)
            score = 1.0 - distances[i] if distances[i] is not None else 0.0
            formatted.append({
                'entity_id': ids[i],
                'score': score,
                'metadata': metadatas[i]
            })
            
        return formatted
