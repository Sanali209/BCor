import pytest
import os
from src.apps.experemental.imgededupe.core.infrastructure.database import DatabaseManager
from src.apps.experemental.imgededupe.core.infrastructure.uow import SqliteUnitOfWork
from src.apps.experemental.imgededupe.core.domain.entities import ImageFile, Cluster, ImageRelation

@pytest.fixture
def db_manager(tmp_path):
    db_path = str(tmp_path / "test_imgededupe.db")
    return DatabaseManager(db_path)

@pytest.mark.asyncio
async def test_image_repository_crud(db_manager):
    uow = SqliteUnitOfWork(db_manager)
    
    async with uow:
        image = ImageFile(
            path="test/path.jpg",
            phash="deadbeef",
            file_size=1024,
            width=100,
            height=100,
            mtime=1234.56
        )
        uow.images.save(image)
        await uow.commit()

    async with uow:
        retrieved = uow.images.get_by_path("test/path.jpg")
        assert retrieved is not None
        assert retrieved.phash == "deadbeef"
        assert retrieved.file_size == 1024
        assert retrieved.is_deleted is False

@pytest.mark.asyncio
async def test_relation_repository(db_manager):
    uow = SqliteUnitOfWork(db_manager)
    
    async with uow:
        # Save images first (due to FK)
        uow.images.save(ImageFile(path="a.jpg"))
        uow.images.save(ImageFile(path="b.jpg"))
        
        rel = ImageRelation(
            file1_path="a.jpg",
            file2_path="b.jpg",
            relation_type="duplicate",
            score=1.0
        )
        uow.relations.save(rel)
        await uow.commit()

    async with uow:
        relations = uow.relations.get_relations_for_file("a.jpg")
        assert len(relations) == 1
        assert relations[0].file2_path == "b.jpg"

@pytest.mark.asyncio
async def test_cluster_repository(db_manager):
    uow = SqliteUnitOfWork(db_manager)
    
    async with uow:
        uow.images.save(ImageFile(path="img1.jpg"))
        uow.images.save(ImageFile(path="img2.jpg"))
        
        cluster = Cluster(
            id="c1",
            name="Test Cluster",
            file_paths=["img1.jpg", "img2.jpg"]
        )
        uow.clusters.save(cluster)
        await uow.commit()

    async with uow:
        retrieved = uow.clusters._get("c1")
        assert retrieved.name == "Test Cluster"
        assert "img1.jpg" in retrieved.file_paths
        assert "img2.jpg" in retrieved.file_paths
