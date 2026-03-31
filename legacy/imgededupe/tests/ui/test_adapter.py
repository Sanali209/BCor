import pytest
from src.apps.experemental.imgededupe.ui.adapter import GuiEventAdapter
from src.apps.experemental.imgededupe.application.messages import (
    ScanStarted, ScanCompleted, DeduplicationStarted, DuplicatesFound, ClustersGenerated
)

@pytest.fixture
def adapter(qtbot):
    """Fixture to create and track the GuiEventAdapter."""
    adapter = GuiEventAdapter()
    return adapter

def test_adapter_emits_scan_started(adapter, qtbot):
    """Test that the adapter emits signal when scan starts."""
    with qtbot.waitSignal(adapter.scan_started, timeout=1000) as blocker:
        event = ScanStarted(roots=["/test/path"])
        adapter.on_scan_started(event)
    assert blocker.args == [["/test/path"]]

def test_adapter_emits_scan_completed(adapter, qtbot):
    """Test that the adapter emits signal when scan completes."""
    with qtbot.waitSignal(adapter.scan_completed, timeout=1000) as blocker:
        event = ScanCompleted(files_count=100)
        adapter.on_scan_completed(event)
    assert blocker.args == [100]

def test_adapter_emits_dedupe_started(adapter, qtbot):
    """Test that the adapter emits signal when deduplication starts."""
    with qtbot.waitSignal(adapter.dedupe_started, timeout=1000) as blocker:
        event = DeduplicationStarted(engine_type="phash")
        adapter.on_dedupe_started(event)
    assert blocker.args == ["phash"]

def test_adapter_emits_duplicates_found(adapter, qtbot):
    """Test that the adapter emits signal when duplicates are found."""
    with qtbot.waitSignal(adapter.duplicates_found, timeout=1000) as blocker:
        event = DuplicatesFound(relations_count=15)
        adapter.on_duplicates_found(event)
    assert blocker.args == [15]

def test_adapter_emits_clusters_generated(adapter, qtbot):
    """Test that the adapter emits signal when clusters are generated."""
    with qtbot.waitSignal(adapter.clusters_generated, timeout=1000) as blocker:
        event = ClustersGenerated(clusters_count=5)
        adapter.on_clusters_generated(event)
    assert blocker.args == [5]
