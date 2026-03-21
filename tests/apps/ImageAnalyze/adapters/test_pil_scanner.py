import pytest
from PIL import Image

from src.apps.ImageAnalyze.adapters.scanners.pil_scanner import PILScanner


@pytest.fixture
def test_image(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (100, 200), color="red")
    img.save(img_path)
    return img_path


def test_pil_scanner_scan_file(test_image):
    # Arrange
    scanner = PILScanner()

    # Act
    metadata = scanner.scan_file(str(test_image))

    # Assert
    assert metadata is not None
    assert metadata.filename == "test.png"
    assert metadata.width == 100
    assert metadata.height == 200
    assert metadata.extension == ".png"


def test_pil_scanner_scan_directory(tmp_path, test_image):
    # Arrange
    scanner = PILScanner()

    # Act
    results = scanner.scan_directory(str(tmp_path))

    # Assert
    assert len(results) == 1
    assert results[0].filename == "test.png"
