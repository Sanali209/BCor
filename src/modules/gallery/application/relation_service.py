import logging
from typing import List, Optional
from uuid import UUID, uuid4

from ..domain.entities import RelationRecord
from .uow import GalleryUnitOfWork

logger = logging.getLogger(__name__)


class RelationService:
    """Service to manage universal relations between gallery entities."""

    def __init__(self, uow: GalleryUnitOfWork) -> None:
        self.uow = uow

    async def create_relation(
        self, 
        from_id: str, 
        from_type: str, 
        to_id: str, 
        to_type: str, 
        relation_type: str,
        confidence: float = 1.0,
        metadata: Optional[dict] = None
    ) -> RelationRecord:
        """
        Creates a new relation. 
        Note: True bidirectional relations in this system are handled by querying 
        both directions in the repository.
        """
        async with self.uow:
            relation = RelationRecord(
                id=uuid4(),
                from_entity_type=from_type,
                from_id=from_id,
                to_entity_type=to_type,
                to_id=to_id,
                relation_type_code=relation_type,
                confidence=confidence,
                metadata=metadata or {}
            )
            self.uow.relations.save(relation)
            self.uow.commit()
            return relation

    async def get_relations(self, entity_id: str, entity_type: str) -> List[RelationRecord]:
        """Retrieves all relations involving the specified entity."""
        async with self.uow:
            return self.uow.relations.find_by_entity(entity_id, entity_type)

    async def delete_relation(self, relation_id: UUID) -> None:
        """Deletes a specific relation."""
        async with self.uow:
            self.uow.relations.delete(relation_id)
            self.uow.commit()
