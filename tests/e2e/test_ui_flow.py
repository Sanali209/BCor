import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt, QItemSelectionModel
from PySide6.QtWidgets import QWidget, QPushButton
from src.apps.experemental.declarative_imgededupe.ui.AppWindow import AppWindow
from src.core.messagebus import MessageBus

@pytest.fixture
def mock_bus():
    return MagicMock(spec=MessageBus)

def test_session_setup_to_explorer_flow(qtbot, mock_bus):
    """
    Test the full flow from scan setup to cluster explorer.
    """
    window = AppWindow(bus=mock_bus)
    window.show()
    qtbot.addWidget(window)
    
    setup_widget = window.setup_view
    
    # Wire the signal to transition for the test (simulating gui.py logic)
    setup_widget.start_scan.connect(lambda r, t, e: window.stack.setCurrentIndex(1))
    
    # 1. Add a folder (mocking the dialog)
    with patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory", return_value="/fake/path"):
        qtbot.mouseClick(setup_widget.add_btn, Qt.LeftButton)
        
    assert setup_widget.root_list.count() == 1
    assert setup_widget.root_list.item(0).text() == "/fake/path"
    
    # 2. Start the scan
    qtbot.mouseClick(setup_widget.start_btn, Qt.LeftButton)
    
    # Verify transition (wait for async update)
    qtbot.waitUntil(lambda: window.stack.currentIndex() == 1, timeout=2000)
    explorer = window.explorer_view
    assert explorer.isVisible()

def test_setup_validation(qtbot, mock_bus):
    """
    Ensure scan doesn't start with empty paths.
    """
    window = AppWindow(bus=mock_bus)
    window.show()
    qtbot.addWidget(window)
    
    setup_widget = window.setup_view
    
    # Clicking start without any paths
    qtbot.mouseClick(setup_widget.start_btn, Qt.LeftButton)
    
    # Should still be on page 0
    assert window.stack.currentIndex() == 0

def test_cluster_explorer_interaction(qtbot, mock_bus):
    """
    Verify that selecting a cluster member updates the detail view.
    """
    from src.modules.assets.domain.models import ImageAsset
    
    window = AppWindow(bus=mock_bus)
    window.show()
    qtbot.addWidget(window)
    
    # Force switch to explorer
    window.stack.setCurrentIndex(1)
    explorer = window.explorer_view
    
    # Inject mock data
    mock_assets = [
        ImageAsset(id="1", uri="file:///path/1.jpg", name="1.jpg", mime_type="image/jpeg", description="", content_hash="abc", size=102400),
        ImageAsset(id="2", uri="file:///path/2.jpg", name="2.jpg", mime_type="image/jpeg", description="", content_hash="def", size=204800)
    ]
    explorer.table.model().update_items(mock_assets)
    
    # Select first row
    index = explorer.table.model().index(0, 0)
    explorer.table.clicked.emit(index)
    explorer.table.setCurrentIndex(index) # Simulate UI selection
    
    # Verify card was added
    assert explorer.card_layout.count() == 1
    
    # 3. Confirm Duplicate
    with qtbot.waitSignal(explorer.confirm_duplicate, timeout=1000) as blocker:
        qtbot.mouseClick(explorer.merge_btn, Qt.LeftButton)
        
    assert blocker.args == ["1"] # ID of first mock asset

def test_pairwise_navigation_flow(qtbot, mock_bus):
    """Verify that clicking Compare Pairwise opens the PairwiseView."""
    from src.modules.assets.domain.models import ImageAsset, SimilarTo
    
    window = AppWindow(bus=mock_bus)
    window.show()
    qtbot.addWidget(window)
    
    explorer = window.explorer_view
    window.stack.setCurrentIndex(1)
    
    # Inject mock asset with similarity
    asset = ImageAsset(id="a1", uri="file:///1.jpg", name="1.jpg", mime_type="image/jpeg", description="", content_hash="h1")
    asset.similar.append(SimilarTo(id="a2", score=0.9))
    explorer.table.model().update_items([asset])
    
    # Select and click compare
    index = explorer.table.model().index(0, 0)
    explorer.table.setCurrentIndex(index)
    flags = QItemSelectionModel.Select | QItemSelectionModel.Rows
    explorer.table.selectionModel().select(index, flags)
    
    # Wire pairwise signal (simulating open_pairwise in gui.py)
    def mock_open_pairwise(a, b_id):
        from src.modules.assets.domain.models import ImageAsset
        b = ImageAsset(id=b_id, uri=f"file:///{b_id}.jpg", name=f"{b_id}.jpg", mime_type="image/jpeg", description="", content_hash="h2")
        window.pairwise_view.set_pair(a, b)
        window.stack.setCurrentIndex(2)
        
    explorer.compare_pair.connect(mock_open_pairwise)
    
    qtbot.mouseClick(explorer.compare_btn, Qt.LeftButton)
    
    # Verify transition to PairwiseView (Index 2)
    qtbot.waitUntil(lambda: window.stack.currentIndex() == 2, timeout=2000)
    assert window.pairwise_view.isVisible()
    assert window.pairwise_view.info_label.text() != "Compare assets"

def test_pairwise_annotation_signal(qtbot, mock_bus):
    """Verify that annotation buttons in PairwiseView emit signals."""
    from src.modules.assets.domain.models import ImageAsset, RelationType
    
    window = AppWindow(bus=mock_bus)
    window.show()
    qtbot.addWidget(window)
    
    pairwise = window.pairwise_view
    a = ImageAsset(id="a1", uri="file:///1.jpg", name="1.jpg", mime_type="image/jpeg", description="", content_hash="h1")
    b = ImageAsset(id="a2", uri="file:///2.jpg", name="2.jpg", mime_type="image/jpeg", description="", content_hash="h2")
    pairwise.set_pair(a, b)
    
    # Spy on annotated signal
    with qtbot.waitSignal(pairwise.annotated, timeout=1000) as blocker:
        # Find first button in the grid (Duplicate) and click it
        buttons = pairwise.findChildren(QPushButton)
        dup_btn = next(btn for btn in buttons if "Duplicate" in btn.text())
        qtbot.mouseClick(dup_btn, Qt.LeftButton)
        
    assert blocker.args[0] == "a2"
    assert str(blocker.args[1]) == str(RelationType.DUPLICATE)

def test_pairwise_deletion_signal(qtbot, mock_bus):
    """Verify that deletion buttons in PairwiseView emit signals."""
    from src.modules.assets.domain.models import ImageAsset
    
    window = AppWindow(bus=mock_bus)
    window.show()
    qtbot.addWidget(window)
    
    pairwise = window.pairwise_view
    a = ImageAsset(id="a1", uri="file:///1.jpg", name="1.jpg", mime_type="image/jpeg", description="", content_hash="h1")
    b = ImageAsset(id="a2", uri="file:///2.jpg", name="2.jpg", mime_type="image/jpeg", description="", content_hash="h2")
    pairwise.set_pair(a, b)
    
    with qtbot.waitSignal(pairwise.deleted, timeout=1000) as blocker:
        qtbot.mouseClick(pairwise.btn_del_a, Qt.LeftButton)
        
    assert blocker.args == ["a1"]

def test_undo_action_trigger(qtbot, mock_bus):
    """Verify that the Undo action in the toolbar is connected."""
    window = AppWindow(bus=mock_bus)
    window.show()
    qtbot.addWidget(window)
    
    # Spy on the signal
    with qtbot.waitSignal(window.undo_act.triggered, timeout=1000):
        window.undo_act.trigger()
