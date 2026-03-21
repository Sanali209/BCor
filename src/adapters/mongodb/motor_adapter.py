from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

class MotorMongoAdapter:
    def __init__(self, host: str, port: int, database: str):
        self.client = AsyncIOMotorClient(host, port)
        self.db = self.client[database]

    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.db[collection].find_one(query)

    async def find(self, collection: str, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        cursor = self.db[collection].find(query).limit(limit)
        return await cursor.to_list(length=limit)

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        result = await self.db[collection].insert_one(document)
        return str(result.inserted_id)

    async def update_one(self, collection: str, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        await self.db[collection].update_one(query, {"$set": update}, upsert=upsert)

    async def delete_one(self, collection: str, query: Dict[str, Any]):
        await self.db[collection].delete_one(query)
        
    def close(self):
        self.client.close()
