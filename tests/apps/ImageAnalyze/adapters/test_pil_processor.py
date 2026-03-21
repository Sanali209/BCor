import os

import pytest
from PIL import Image

from src.apps.ImageAnalyze.adapters.processors.pil_processor import PILImageProcessor
from src.apps.ImageAnalyze.domain.entities.batch_processing import (
    ConvertAction,
    DeleteAction,
    ScaleAction,
)
from src.apps.ImageAnalyze.domain.entities.image_metadata import ImageMetadata


@pytest.fixture
def test_image(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(img_path)
    return ImageMetadata(
        path=str(img_path),
        filename="test.png",
        extension=".png",
        size_bytes=os.path.getsize(img_path),
        width=100,
        height=100,
    )


def test_pil_processor_delete(test_image):
    # Arrange
    processor = PILImageProcessor()
    action = DeleteAction()

    # Act
    result = processor.execute(test_image, action)

    # Assert
    assert result.success == True
    assert result.action_taken == "DELETE"
    assert not os.path.exists(test_image.path)


def test_pil_processor_scale(test_image):
    # Arrange
    processor = PILImageProcessor()
    action = ScaleAction(max_width=50, max_height=50)

    # Act
    result = processor.execute(test_image, action)

    # Assert
    assert result.success == True
    with Image.open(test_image.path) as img:
        assert img.size == (50, 50)


def test_pil_processor_convert(test_image):
    # Arrange
    processor = PILImageProcessor()
    action = ConvertAction(target_format=".jpg", delete_original=True)

    # Act
    result = processor.execute(test_image, action)

    # Assert
    assert result.success == True
    assert result.new_path.endswith(".jpg")
    assert os.path.exists(result.new_path)
    assert not os.path.exists(test_image.path)
