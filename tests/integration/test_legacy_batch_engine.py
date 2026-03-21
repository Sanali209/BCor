import pytest
import os
import sys
from pathlib import Path

# Fix path to include legacy image analize
LEGACY_PATH = Path(r"d:\github\BCor\src\legacy_to_port\image analize")
sys.path.append(str(LEGACY_PATH))

from core.batch_engine import BatchEngine, Rule, AreaCondition, DeleteAction, ProcessingResult

def test_legacy_batch_engine_logic(tmp_path):
    """Verify the logic of the legacy BatchEngine before porting."""
    # Create dummy images
    img1 = tmp_path / "small.png"
    img1.write_text("dummy")
    
    img2 = tmp_path / "large.png"
    img2.write_text("dummy" * 100)
    
    # Mock image records as the DB would return them
    images = [
        {"path": str(img1), "area": 100, "size_bytes": 5},
        {"path": str(img2), "area": 10000, "size_bytes": 500},
    ]
    
    # Define a rule: Delete images with area > 5000
    rule = Rule(
        condition=AreaCondition(min_area=5001),
        action=DeleteAction(),
        name="DeleteLargeImages"
    )
    
    engine = BatchEngine()
    
    # Dry run
    results = engine.execute_rules(images, [rule], dry_run=True)
    
    assert len(results) == 1
    assert results[0].original_path == str(img2)
    assert results[0].action_taken == "DELETE"
    assert results[0].success is True
    assert img2.exists()  # Dry run should not delete
    
    # Real run
    results = engine.execute_rules(images, [rule], dry_run=False)
    assert len(results) == 1
    assert not img2.exists()  # File should be gone
    assert img1.exists()     # File should remain

if __name__ == "__main__":
    pytest.main([__file__])
