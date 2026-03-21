import pytest
from uuid import uuid4
from datetime import datetime
from src.modules.gallery.domain.entities import Image, Category, RelationRecord


def test_image_entity_creation():
    image_id = uuid4()
    image = Image(
        id=image_id,
        file_path="/path/to/image.jpg",
        title="Test Image",
        description="A test image description",
        uploaded_at=datetime.now()
    )
    assert image.id == image_id
    assert image.title == "Test Image"
    assert image.rating == 0.0


def test_image_rating_calculation():
    image = Image(rating_sum=15, rating_count=3)
    assert image.rating == 5.0
    
    image_no_ratings = Image(rating_sum=0, rating_count=0)
    assert image_no_ratings.rating == 0.0


def test_category_entity_creation():
    cat_id = uuid4()
    category = Category(
        id=cat_id,
        name="Nature",
        slug="nature",
        full_path="Nature"
    )
    assert category.id == cat_id
    assert category.name == "Nature"
    assert category.age_restriction == "G"


def test_relation_record_creation():
    rel_id = uuid4()
    relation = RelationRecord(
        id=rel_id,
        from_entity_type="image",
        from_id="img1",
        to_entity_type="person",
        to_id="p1",
        relation_type_code="depicts",
        confidence=0.95
    )
    assert relation.id == rel_id
    assert relation.confidence == 0.95
