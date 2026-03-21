from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..entities import Image, Category, RelationRecord, Detection

class ImageRepository(ABC):
    @abstractmethod
    def save(self, image: Image) -> None:
        pass

    @abstractmethod
    def get_by_id(self, image_id: UUID) -> Optional[Image]:
        pass

    @abstractmethod
    def find_all(self, filters: Dict[str, Any]) -> List[Image]:
        pass
    @abstractmethod
    def find_by_hash(self, md5_hash: str) -> Optional[Image]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, image_id: UUID) -> None:
        pass


class CategoryRepository(ABC):
    @abstractmethod
    def save(self, category: Category) -> None:
        pass

    @abstractmethod
    def get_by_id(self, category_id: UUID) -> Optional[Category]:
        pass

    @abstractmethod
    def get_by_slug(self, slug: str) -> Optional[Category]:
        pass

    @abstractmethod
    def find_all(self) -> List[Category]:
        pass


class RelationRepository(ABC):
    @abstractmethod
    def save(self, relation: RelationRecord) -> None:
        pass

    @abstractmethod
    def find_by_entity(self, entity_id: str, entity_type: str) -> List[RelationRecord]:
        pass

    @abstractmethod
    def delete(self, relation_id: UUID) -> None:
        pass


class VectorSearchProvider(ABC):
    @abstractmethod
    def search_similar_text(self, text: str, model: str, limit: int = 100) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def search_similar_image(self, image_id: UUID, model: str, limit: int = 100) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def add_vector(self, image_id: UUID, vector: List[float], model: str, metadata: Dict[str, Any]) -> None:
        pass
