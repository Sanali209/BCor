from unittest.mock import MagicMock

import pytest

from src.apps.ImageAnalyze.domain.entities.image_metadata import ImageMetadata
from src.apps.ImageAnalyze.domain.interfaces.i_image_scanner import IImageScanner
from src.apps.ImageAnalyze.use_cases.scan_directory import ScanDirectoryUseCase


@pytest.mark.asyncio
async def test_scan_directory_use_case_executes_successfully():
    # Arrange
    mock_scanner = MagicMock(spec=IImageScanner)
    mock_metadata = ImageMetadata(
        path="/path/to/img.jpg", filename="img.jpg", extension=".jpg", size_bytes=100, width=10, height=10
    )
    mock_scanner.scan_directory.return_value = [mock_metadata]

    use_case = ScanDirectoryUseCase(scanner=mock_scanner)
    directory = "/some/dir"

    # Act
    results = await use_case.execute(directory)

    # Assert
    assert len(results) == 1
    assert results[0] == mock_metadata
    mock_scanner.scan_directory.assert_called_once_with(directory)
