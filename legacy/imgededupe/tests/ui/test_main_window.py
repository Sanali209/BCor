import pytest
from unittest.mock import MagicMock
from src.apps.experemental.imgededupe.ui.mainwindow import MainWindow
from src.apps.experemental.imgededupe.ui.adapter import GuiEventAdapter

@pytest.fixture
def adapter():
    return GuiEventAdapter()

@pytest.fixture
def main_window(adapter):
    # Mocking dependencies for MainWindow
    session = MagicMock()
    file_repo = MagicMock()
    cluster_repo = MagicMock()
    db_manager = MagicMock()
    
    # We need to pass the adapter and bus now
    bus = MagicMock()
    return MainWindow(session, file_repo, cluster_repo, db_manager, adapter=adapter, bus=bus)

def test_mainwindow_switches_to_progress_on_scan_started(main_window, adapter, qtbot):
    """
    Test that MainWindow reacts to GuiEventAdapter signals.
    """
    qtbot.addWidget(main_window)
    
    # Initial index should be 0 (Setup)
    assert main_window.stack.currentIndex() == 0
    
    # Emit signal from adapter
    adapter.scan_started.emit(["/test"])
    
    # MainWindow should switch to index 1 (Progress)
    assert main_window.stack.currentIndex() == 1
