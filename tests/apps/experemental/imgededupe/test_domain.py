import pytest
from src.apps.experemental.imgededupe.core.domain.entities import ImageFile, ImageRelation
from src.apps.experemental.imgededupe.core.domain.messages import StartScanCommand, ScanProgressEvent

def test_image_file_validation():
    file = ImageFile(path="/test/path.jpg", file_size=1024)
    assert file.path == "/test/path.jpg"
    assert file.width == 0
    assert file.is_deleted is False

def test_start_scan_command_defaults():
    cmd = StartScanCommand(roots=["/root"])
    assert cmd.engine_type == "phash"
    assert cmd.threshold == 5
    assert cmd.roots == ["/root"]

def test_scan_progress_event():
    evt = ScanProgressEvent(current=10, total=100, message="Scanning...")
    assert evt.current == 10
    assert evt.total == 100
    assert evt.message == "Scanning..."
