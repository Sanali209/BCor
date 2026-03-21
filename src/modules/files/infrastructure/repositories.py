from typing import List, Optional
from src.adapters.mongodb.motor_adapter import MotorMongoAdapter
from src.modules.files.domain.models import FileModel

class FileRepository:
    def __init__(self, adapter: MotorMongoAdapter, collection: str = "files"):
        self.adapter = adapter
        self.collection = collection

    async def get_by_path(self, path: str) -> Optional[FileModel]:
        data = await self.adapter.find_one(self.collection, {"local_path": path})
        if data:
            return FileModel(**data)
        return None

    async def save(self, file: FileModel):
        data = file.model_dump(by_alias=True, exclude_none=True)
        if file.id:
            await self.adapter.update_one(self.collection, {"_id": file.id}, data, upsert=True)
        else:
            file.id = await self.adapter.insert_one(self.collection, data)

    async def find_by_tags(self, tags: List[str]) -> List[FileModel]:
        data_list = await self.adapter.find(self.collection, {"tags": {"$all": tags}})
        return [FileModel(**d) for d in data_list]
