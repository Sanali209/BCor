from __future__ import annotations
import logging
from typing import List, Optional, Dict, Any, cast
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from ..domain.models import RelationRecord, RelationSubType

logger = logging.getLogger(__name__)

class MongoRelationRepo:
    def __init__(self, db_url: str = "mongodb://localhost:27017", db_name: str = "files_db") -> None:
        self.client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(db_url)
        self.db = self.client[db_name]
        self.collection = self.db["relation_records"]

    def _to_record(self, doc: Dict[str, Any]) -> RelationRecord:
        return RelationRecord(
            id=str(doc["_id"]),
            from_id=str(doc["from_id"]),
            to_id=str(doc["to_id"]),
            relation_type=doc.get("type", "similar_search"),
            sub_type=RelationSubType(doc.get("sub_type", "none")),
            distance=doc.get("distance", 0.0),
            euclidean=doc.get("euclidean", 0.0),
            manhattan=doc.get("manhattan", 0.0),
            hamming=doc.get("hamming", 0.0),
            dot=doc.get("dot", 0.0),
            emb_type=doc.get("emb_type", "unknown")
        )

    async def get_by_id(self, record_id: str) -> Optional[RelationRecord]:
        doc = await self.collection.find_one({"_id": ObjectId(record_id)})
        return self._to_record(doc) if doc else None

    async def find_relations(self, query: Dict[str, Any], limit: int = 100) -> List[RelationRecord]:
        cursor = self.collection.find(query).limit(limit)
        return [self._to_record(doc) async for doc in cursor]

    async def save(self, record: RelationRecord) -> str:
        doc = {
            "from_id": ObjectId(record.from_id),
            "to_id": ObjectId(record.to_id),
            "type": record.relation_type,
            "sub_type": record.sub_type.value,
            "distance": record.distance,
            "euclidean": record.euclidean,
            "manhattan": record.manhattan,
            "hamming": record.hamming,
            "dot": record.dot,
            "emb_type": record.emb_type,
            "updated_at": record.created_at
        }
        if record.id:
            await self.collection.update_one({"_id": ObjectId(record.id)}, {"$set": doc})
            return record.id
        else:
            result = await self.collection.insert_one(doc)
            return str(result.inserted_id)

    async def delete(self, record_id: str) -> None:
        await self.collection.delete_one({"_id": ObjectId(record_id)})

    async def get_or_create(self, from_id: str, to_id: str, rel_type: str = "similar_search") -> RelationRecord:
        query = {"from_id": ObjectId(from_id), "to_id": ObjectId(to_id), "type": rel_type}
        doc = await self.collection.find_one(query)
        if doc:
            return self._to_record(doc)
        
        # Symmetrical check
        query_sym = {"from_id": ObjectId(to_id), "to_id": ObjectId(from_id), "type": rel_type}
        doc_sym = await self.collection.find_one(query_sym)
        if doc_sym:
             return self._to_record(doc_sym)
        
        record = RelationRecord(id="", from_id=from_id, to_id=to_id, relation_type=rel_type)
        new_id = await self.save(record)
        return RelationRecord(
            id=new_id,
            from_id=record.from_id,
            to_id=record.to_id,
            relation_type=record.relation_type,
            sub_type=record.sub_type,
            distance=record.distance,
            euclidean=record.euclidean,
            manhattan=record.manhattan,
            hamming=record.hamming,
            dot=record.dot,
            emb_type=record.emb_type,
            created_at=record.created_at
        )
