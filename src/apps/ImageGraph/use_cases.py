from __future__ import annotations
from typing import List, Dict, Any, Optional
from bson import ObjectId
from .domain.models import RelationRecord, RelationSubType
from .infrastructure.mongo_relation_repo import MongoRelationRepo

class SearchRelatedImagesUseCase:
    def __init__(self, relation_repo: MongoRelationRepo, file_repo: Any) -> None:
        self.relation_repo = relation_repo
        self.file_repo = file_repo

    async def execute(self, file_id: str, threshold: float = 0.5) -> List[Dict[str, Any]]:
        query = {
            "from_id": ObjectId(file_id),
            "distance": {"$gt": threshold},
            "sub_type": {"$ne": "wrong"}
        }
        relations = await self.relation_repo.find_relations(query)
        results = []
        for rel in relations:
            target_file = await self.file_repo.get_by_id(rel.to_id)
            if target_file:
                results.append({
                    "relation": rel,
                    "file": target_file
                })
        return results

class UpdateRelationUseCase:
    def __init__(self, relation_repo: MongoRelationRepo) -> None:
        self.relation_repo = relation_repo

    async def execute(self, relation_id: str, new_sub_type: RelationSubType) -> None:
        relation = await self.relation_repo.get_by_id(relation_id)
        if not relation:
            return
        
        updated = RelationRecord(
            id=relation.id,
            from_id=relation.from_id,
            to_id=relation.to_id,
            relation_type=relation.relation_type,
            sub_type=new_sub_type,
            distance=relation.distance,
            emb_type=relation.emb_type
        )
        await self.relation_repo.save(updated)
        
        # Symmetrical update (legacy pattern)
        query_sym = {"from_id": ObjectId(relation.to_id), "to_id": ObjectId(relation.from_id), "type": relation.relation_type}
        sym_rels = await self.relation_repo.find_relations(query_sym)
        for sym_rel in sym_rels:
             sym_updated = RelationRecord(
                id=sym_rel.id,
                from_id=sym_rel.from_id,
                to_id=sym_rel.to_id,
                relation_type=sym_rel.relation_type,
                sub_type=new_sub_type,
                distance=sym_rel.distance,
                emb_type=sym_rel.emb_type
            )
             await self.relation_repo.save(sym_updated)

class CreateManualRelationUseCase:
    def __init__(self, relation_repo: MongoRelationRepo) -> None:
        self.relation_repo = relation_repo

    async def execute(self, from_id: str, to_id: str) -> RelationRecord:
        return await self.relation_repo.get_or_create(from_id, to_id, "manual")
