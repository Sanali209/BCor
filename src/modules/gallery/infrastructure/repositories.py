from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from src.core.repository import AbstractRepository
from ..domain.entities import Category, Image, RelationRecord
from ..domain.interfaces import ImageRepository, CategoryRepository, RelationRepository


class SqlImageRepository(AbstractRepository[Image], ImageRepository):
    """SQLAlchemy implementation of ImageRepository."""

    def __init__(self, session: Session) -> None:
        super().__init__()
        self.session = session

    def _add(self, image: Image) -> None:
        self.session.add(image)

    def _get(self, reference: str) -> Optional[Image]:
        return self.session.get(Image, UUID(reference))

    def save(self, image: Image) -> None:
        self.add(image)

    def get_by_id(self, image_id: UUID) -> Optional[Image]:
        return self.get(str(image_id))

    def find_all(self, filters: Dict[str, Any]) -> List[Image]:
        stmt = select(Image)
        # In a real implementation, we would apply filters here
        # For now, this is a basic stub
        return list(self.session.scalars(stmt).all())

    def delete(self, image_id: UUID) -> None:
        image = self.get_by_id(image_id)
        if image:
            self.session.delete(image)

    def find_by_hash(self, md5_hash: str) -> Optional[Image]:
        stmt = select(Image).where(Image.md5_hash == md5_hash)
        return self.session.scalars(stmt).first()


class SqlCategoryRepository(CategoryRepository):
    """SQLAlchemy implementation of CategoryRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, category: Category) -> None:
        self.session.add(category)

    def get_by_id(self, category_id: UUID) -> Optional[Category]:
        return self.session.get(Category, category_id)

    def get_by_slug(self, slug: str) -> Optional[Category]:
        stmt = select(Category).where(Category.slug == slug)
        return self.session.scalars(stmt).first()

    def find_all(self) -> List[Category]:
        stmt = select(Category).order_by(Category.sort_order)
        return list(self.session.scalars(stmt).all())


class SqlRelationRepository(RelationRepository):
    """SQLAlchemy implementation of RelationRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, relation: RelationRecord) -> None:
        self.session.add(relation)

    def find_by_entity(self, entity_id: str, entity_type: str) -> List[RelationRecord]:
        stmt = select(RelationRecord).where(
            ((RelationRecord.from_id == entity_id) & (RelationRecord.from_entity_type == entity_type)) |
            ((RelationRecord.to_id == entity_id) & (RelationRecord.to_entity_type == entity_type))
        )
        return list(self.session.scalars(stmt).all())

    def delete(self, relation_id: UUID) -> None:
        stmt = delete(RelationRecord).where(RelationRecord.id == relation_id)
        self.session.execute(stmt)
