import pytest

from src.apps.ImageAnalyze.domain.entities.image_metadata import ImageMetadata


def test_image_metadata_creation():
    # Arrange & Act
    metadata = ImageMetadata(
        path="/path/to/image.jpg", filename="image.jpg", extension=".jpg", size_bytes=1024, width=800, height=600
    )

    # Assert
    assert metadata.path == "/path/to/image.jpg"
    assert metadata.filename == "image.jpg"
    assert metadata.extension == ".jpg"
    assert metadata.size_bytes == 1024
    assert metadata.width == 800
    assert metadata.height == 600


def test_image_metadata_is_immutable():
    # Arrange
    metadata = ImageMetadata(
        path="/path/to/image.jpg", filename="image.jpg", extension=".jpg", size_bytes=1024, width=800, height=600
    )

    # Act & Assert
    with pytest.raises(AttributeError):
        metadata.path = "/new/path.jpg"
