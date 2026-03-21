import pytest
from pathlib import Path
from src.apps.ImageAnalyze.domain.models import ImageAnalysisRecord, ConflictStrategy
from src.apps.ImageAnalyze.domain.rules import AreaCondition, DeleteAction, ConvertAction

def test_area_condition():
    record = ImageAnalysisRecord(
        path="test.jpg",
        filename="test",
        extension=".jpg",
        size_bytes=100,
        width=100,
        height=100
    )
    
    cond = AreaCondition(min_area=5000)
    assert cond.evaluate(record) is True
    
    cond_false = AreaCondition(min_area=20000)
    assert cond_false.evaluate(record) is False

def test_delete_action(tmp_path):
    img_path = tmp_path / "test.jpg"
    img_path.write_text("data")
    
    record = ImageAnalysisRecord(
        path=str(img_path),
        filename="test",
        extension=".jpg",
        size_bytes=4,
        width=10,
        height=10
    )
    
    action = DeleteAction()
    
    # Dry run
    res = action.execute(record, dry_run=True)
    assert res.success is True
    assert img_path.exists()
    
    # Real run
    res = action.execute(record, dry_run=False)
    assert res.success is True
    assert not img_path.exists()

def test_convert_action_dry_run(tmp_path):
    img_path = tmp_path / "test.png"
    img_path.write_text("data")
    
    record = ImageAnalysisRecord(
        path=str(img_path),
        filename="test",
        extension=".png",
        size_bytes=4,
        width=10,
        height=10
    )
    
    action = ConvertAction(target_format=".jpg")
    res = action.execute(record, dry_run=True)
    
    assert res.success is True
    assert res.action_taken.startswith("CONVERT")
    assert res.new_path.endswith(".jpg")
