import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class ChromaAdapter:
    """Adapter for interacting with Chroma vector database."""

    def __init__(self, path: str = "./chroma_db", host: Optional[str] = None, port: Optional[int] = None) -> None:
        """
        Initialize Chroma client.
        
        Args:
            path: Path for persistent storage (local mode)
            host: Chroma server host (client/server mode)
            port: Chroma server port
        """
        if host and port:
            self.client = chromadb.HttpClient(host=host, port=port, settings=Settings(allow_reset=True))
        else:
            self.client = chromadb.PersistentClient(path=path)

    def get_or_create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Collection:
        """Get an existing collection or create a new one."""
        return self.client.get_or_create_collection(
            name=name, 
            metadata=metadata or {"hnsw:space": "cosine"}
        )

    def add_vectors(
        self, 
        collection_name: str, 
        ids: List[str], 
        embeddings: List[List[float]], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        documents: Optional[List[str]] = None
    ) -> None:
        """Add vectors to a specific collection."""
        collection = self.get_or_create_collection(collection_name)
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )

    def query_similar(
        self, 
        collection_name: str, 
        query_embeddings: List[List[float]], 
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query for similar vectors."""
        collection = self.get_or_create_collection(collection_name)
        return collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where
        )

    def delete_by_ids(self, collection_name: str, ids: List[str]) -> None:
        """Delete vectors by their IDs."""
        collection = self.get_or_create_collection(collection_name)
        collection.delete(ids=ids)

    def get_by_ids(self, collection_name: str, ids: List[str]) -> Dict[str, Any]:
        """Retrieve vectors and metadata by IDs."""
        collection = self.get_or_create_collection(collection_name)
        return collection.get(ids=ids)
