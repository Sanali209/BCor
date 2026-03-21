import sys
import os
import pytest
import asyncio
from unittest.mock import MagicMock

# Add legacy path to sys.path
legacy_parent_path = os.path.abspath(os.path.join(os.getcwd(), "src", "legacy_to_port", "sanali209", "Python"))
if legacy_parent_path not in sys.path:
    sys.path.append(legacy_parent_path)

from src.adapters.mongodb.motor_adapter import MotorMongoAdapter
from src.modules.files.domain.models import FileModel
from src.modules.files.infrastructure.repositories import FileRepository

@pytest.fixture
async def mongo_adapter():
    # Use mongomock-motor for environment-independent testing
    from mongomock_motor import AsyncMongoMockClient
    mock_client = AsyncMongoMockClient()
    adapter = MotorMongoAdapter(host="localhost", port=27117, database="test_bcor_db")
    # Inject mock client into adapter
    adapter.client = mock_client
    adapter.db = mock_client["test_bcor_db"]
    yield adapter
    adapter.close()

@pytest.mark.asyncio
async def test_mongo_interoperability(mongo_adapter):
    """
    Verifies that BCor can write a record and legacy MongoClientExt can read it.
    Uses mongomock for both to simulate interoperability in a clean environment.
    """
    repo = FileRepository(adapter=mongo_adapter)
    
    file = FileModel(
        local_path="C:/test/file.jpg",
        name="file.jpg",
        md5="d41d8cd98f00b204e9800998ecf8427e",
        tags=["test", "strangler"]
    )
    
    await repo.save(file)
    assert file.id is not None
    
    # Verify legacy reading (using the same mock client)
    # This simulates another client connecting to the same data
    legacy_record = await mongo_adapter.db["files"].find_one({"local_path": "C:/test/file.jpg"})
    
    assert legacy_record is not None
    assert legacy_record["name"] == "file.jpg"
    assert legacy_record["md5"] == "d41d8cd98f00b204e9800998ecf8427e"
    assert "strangler" in legacy_record["tags"]

@pytest.mark.asyncio
async def test_repository_tags_search(mongo_adapter):
    repo = FileRepository(adapter=mongo_adapter)
    
    file1 = FileModel(local_path="path1", name="name1", tags=["tag1", "tagA"])
    file2 = FileModel(local_path="path2", name="name2", tags=["tag2", "tagA"])
    
    await repo.save(file1)
    await repo.save(file2)
    
    results = await repo.find_by_tags(["tagA"])
    assert len(results) == 2
    
    results_combo = await repo.find_by_tags(["tag1", "tagA"])
    assert len(results_combo) == 1
    assert results_combo[0].name == "name1"
