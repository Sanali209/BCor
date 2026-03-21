import pytest

from src.apps.ImageAnalyze.adapters.repositories.sqlite_repository import SQLiteImageRepository
from src.apps.ImageAnalyze.domain.entities.image_metadata import ImageMetadata


@pytest.fixture
def repo(tmp_path):
    db_path = tmp_path / "test.db"
    return SQLiteImageRepository(str(db_path))


def test_sqlite_repo_save_and_get(repo):
    # Arrange
    img = ImageMetadata("/a.jpg", "a.jpg", ".jpg", 100, 10, 10)

    # Act
    repo.save(img)
    retrieved = repo.get_by_path("/a.jpg")

    # Assert
    assert retrieved is not None
    assert retrieved.filename == "a.jpg"
    assert retrieved.size_bytes == 100


def test_sqlite_repo_save_batch(repo):
    # Arrange
    images = [ImageMetadata("/1.jpg", "1.jpg", ".jpg", 10, 1, 1), ImageMetadata("/2.png", "2.png", ".png", 20, 2, 2)]

    # Act
    repo.save_batch(images)

    # Assert
    stats = repo.get_stats()
    assert stats["total_count"] == 2
    assert stats["total_size_bytes"] == 30


def test_sqlite_repo_record_saving(repo):
    # Act
    repo.record_saving("DELETE", 500, "/deleted.jpg")
    history = repo.get_savings_history()  # Not in interface yet but useful

    # Assert
    assert len(history) == 1
    assert history[0]["saved_bytes"] == 500
