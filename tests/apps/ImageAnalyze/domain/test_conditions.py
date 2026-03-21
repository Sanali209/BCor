import pytest

from src.apps.ImageAnalyze.domain.entities.batch_processing import AreaCondition, FormatCondition, SizeCondition
from src.apps.ImageAnalyze.domain.entities.image_metadata import ImageMetadata


@pytest.fixture
def sample_metadata():
    return ImageMetadata(
        path="/test/img.png", filename="img.png", extension=".png", size_bytes=2000, width=100, height=100
    )


def test_area_condition(sample_metadata):
    # Area = 100 * 100 = 10000
    cond = AreaCondition(min_area=5000, max_area=15000)
    assert cond.evaluate(sample_metadata) == True

    cond_fail = AreaCondition(min_area=15000)
    assert cond_fail.evaluate(sample_metadata) == False


def test_size_condition(sample_metadata):
    cond = SizeCondition(min_bytes=1000, max_bytes=3000)
    assert cond.evaluate(sample_metadata) == True

    cond_small = SizeCondition(max_bytes=1000)
    assert cond_small.evaluate(sample_metadata) == False


def test_format_condition(sample_metadata):
    cond = FormatCondition(target_formats=[".png", ".jpg"])
    assert cond.evaluate(sample_metadata) == True

    cond_not = FormatCondition(target_formats=[".jpg"])
    assert cond_not.evaluate(sample_metadata) == False

    cond_invert = FormatCondition(target_formats=[".jpg"], invert=True)
    assert cond_invert.evaluate(sample_metadata) == True
