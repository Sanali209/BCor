from unittest.mock import MagicMock

import pytest

from src.apps.ImageAnalyze.domain.entities.batch_processing import AreaCondition, DeleteAction, ProcessingResult, Rule
from src.apps.ImageAnalyze.domain.entities.image_metadata import ImageMetadata
from src.apps.ImageAnalyze.domain.interfaces.image_processor import IImageProcessor
from src.apps.ImageAnalyze.use_cases.batch_process import BatchProcessUseCase


@pytest.mark.asyncio
async def test_batch_process_use_case_applies_rules():
    # Arrange
    img = ImageMetadata("/t.png", "t.png", ".png", 100, 10, 10)
    rule = Rule(condition=AreaCondition(min_area=50), action=DeleteAction())

    mock_processor = MagicMock(spec=IImageProcessor)
    mock_processor.execute.return_value = ProcessingResult("/t.png", "DELETE", True)

    use_case = BatchProcessUseCase(processor=mock_processor)

    # Act
    results = await use_case.execute([img], [rule])

    # Assert
    assert len(results) == 1
    assert results[0].action_taken == "DELETE"
    mock_processor.execute.assert_called_once()
