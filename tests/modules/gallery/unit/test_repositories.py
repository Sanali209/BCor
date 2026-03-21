import pytest
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from src.modules.gallery.domain.entities import Image, Category
from src.modules.gallery.infrastructure.models import mapper_registry, start_mappers
from src.modules.gallery.infrastructure.repositories import SqlImageRepository, SqlCategoryRepository


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    mapper_registry.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(in_memory_db):
    try:
        # Clear mappers before starting each test to avoid "already mapped" errors
        clear_mappers()
        start_mappers()
    except Exception:
        pass
        
    Session = sessionmaker(bind=in_memory_db)
    session = Session()
    yield session
    session.close()


def test_repository_can_save_and_get_image(session):
    repo = SqlImageRepository(session)
    image_id = uuid4()
    image = Image(
        id=image_id,
        file_path="/tmp/test.jpg",
        title="Test Image"
    )
    
    repo.save(image)
    session.commit()
    
    retrieved = repo.get_by_id(image_id)
    assert retrieved is not None
    assert retrieved.title == "Test Image"
    assert retrieved.id == image_id


def test_repository_can_save_and_get_category(session):
    repo = SqlCategoryRepository(session)
    cat_id = uuid4()
    category = Category(
        id=cat_id,
        name="Nature",
        slug="nature",
        full_path="Nature"
    )
    
    repo.save(category)
    session.commit()
    
    retrieved = repo.get_by_id(cat_id)
    assert retrieved is not None
    assert retrieved.name == "Nature"
    
    by_slug = repo.get_by_slug("nature")
    assert by_slug.id == cat_id
