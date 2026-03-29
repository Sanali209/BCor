import pytest
from PySide6.QtCore import Qt
from src.apps.experemental.declarative_imgededupe.ui.AppWindow import AppWindow

@pytest.mark.asyncio
async def test_ui_bootstrap(qtbot):
    """
    Verify that the AppWindow initializes and starts in the Setup view.
    """
    from unittest.mock import MagicMock
    from src.core.messagebus import MessageBus
    
    bus = MagicMock(spec=MessageBus)
    window = AppWindow(bus=bus)
    qtbot.addWidget(window)
    
    # Check initial state
    assert window.windowTitle() == "BCor Declarative Deduper"
    assert window.stack.currentIndex() == 0  # Should start at SessionSetup
    
    # Check navigation
    window.stack.setCurrentIndex(1)
    assert window.stack.currentIndex() == 1  # Switched to ClusterExplorer
