import sys
import asyncio
import pytest
import qasync
from unittest.mock import AsyncMock, MagicMock, patch
from dishka import Provider, Scope, provide
from PySide6.QtWidgets import QApplication, QPushButton, QLabel, QListWidget, QLineEdit
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from src.core.system import System
from src.core.module import BaseModule
from src.core.loop_policies import WindowsLoopManager
from src.core.unit_of_work import AbstractUnitOfWork
from src.apps.asset_explorer.main import AssetExplorerDashboard
from src.apps.asset_explorer.module import AssetExplorerModule
from src.modules.agm.module import AGMModule
from src.modules.assets.module import AssetsModule
from src.apps.asset_explorer.presentation.viewmodels.explorer import AssetExplorerViewModel
from src.modules.assets.domain.models import ImageAsset, Asset
from src.modules.agm.mapper import AGMMapper

from neo4j import AsyncDriver, AsyncSession
from src.modules.assets.domain.services import AssetIngestionService
from src.modules.assets.domain.factory import AssetFactory

class MockUoW(AbstractUnitOfWork):
    def _commit(self): pass
    def rollback(self): pass

class TestProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_uow(self) -> AbstractUnitOfWork:
        return MockUoW()
    
    @provide(scope=Scope.APP)
    def provide_neo_driver(self) -> AsyncDriver:
        return MagicMock(spec=AsyncDriver)

    @provide(scope=Scope.REQUEST)
    def provide_neo_session(self) -> AsyncSession:
        return MagicMock(spec=AsyncSession)

    @provide(scope=Scope.APP)
    def provide_asset_factory(self) -> AssetFactory:
        return AssetFactory()

    @provide(scope=Scope.REQUEST)
    def provide_ingest(self) -> AssetIngestionService:
        return MagicMock(spec=AssetIngestionService)

class TestModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.provider = TestProvider()

@pytest.fixture
def qasync_app(qtbot):
    """Fixture to ensure qasync loop is active during the test."""
    WindowsLoopManager.setup_loop()
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    yield app
    if loop.is_running():
        loop.stop()
    if not loop.is_closed():
        loop.close()

@pytest.fixture
async def system_setup():
    """Fixture to bootstrap the framework system for E2E testing."""
    system = System(modules=[AGMModule(), AssetsModule(), AssetExplorerModule(), TestModule()])
    await system.start()
    yield system
    await system.stop()

@pytest.fixture
async def dashboard_view(qasync_app, system_setup, qtbot):
    """Fixture to create and manage the AssetExplorerDashboard with mocked mapper."""
    system = system_setup
    
    # 1. High-Fidelity Mock for AGMMapper
    mock_mapper = MagicMock(spec=AGMMapper)
    mock_query = MagicMock()
    mock_mapper.query.return_value = mock_query
    
    # 2. Mock ImageAsset
    from src.modules.assets.domain.models import Tag
    asset = ImageAsset(
        id="test-123", 
        uri="file:///test.jpg", 
        name="Mock Asset",
        width=1920,
        height=1080
    )
    asset.tags = [Tag(id="t1", name="nature"), Tag(id="t2", name="forest")]
    
    async def mock_all(*args, **kwargs):
        print("DEBUG: mock_all called")
        await asyncio.sleep(0.01)
        return [asset]
    
    mock_query.all = AsyncMock(side_effect=mock_all)
    mock_query.delete = AsyncMock(return_value=1)
    
    # 3. Resolve VM within a scope
    async with system.container() as scope:
        vm = await scope.get(AssetExplorerViewModel)
        vm._mapper = mock_mapper # Use private override to be sure
        
        window = AssetExplorerDashboard(vm)
        qtbot.addWidget(window)
        window.show()
        
        # We need to keep the scope alive while the window is used
        window._scope = scope 
        yield window, vm, mock_mapper

@pytest.mark.asyncio
async def test_dashboard_full_interaction_fw_native(dashboard_view, qtbot):
    """
    Scenario: User searches and selects an asset in the framework-native app.
    Verify: Polymorphic widgets are instantiated correctly.
    """
    window, vm, mock_mapper = dashboard_view
    from src.apps.asset_explorer.main import UrlWidget, TagCloudWidget, NumericWidget
    
    # 1. Search
    qtbot.keyClicks(window.search_panel.query_input, "forest")
    search_btn = next(btn for btn in window.search_panel.findChildren(QPushButton) if "Search" in btn.text())
    qtbot.mouseClick(search_btn, Qt.LeftButton)
    
    # Async Wait for results
    for _ in range(50):
        if window.results_panel.count() >= 1: break
        await asyncio.sleep(0.1)
    
    assert window.results_panel.count() == 1
    item = window.results_panel.item(0)
    
    # 2. Selection
    rect = window.results_panel.visualItemRect(item)
    qtbot.mouseClick(window.results_panel.viewport(), Qt.LeftButton, pos=rect.center())
    
    # Wait for metadata population
    for _ in range(50):
        if window.metadata_panel.child_vm: break
        await asyncio.sleep(0.1)
        
    # 3. Assert Polymorphic Widgets
    # Verify URI uses UrlWidget
    urls = window.metadata_panel.findChildren(UrlWidget)
    assert len(urls) >= 1
    assert "test.jpg" in urls[0].edit.text()
    
    # Verify Tags uses TagCloudWidget
    tag_clouds = window.metadata_panel.findChildren(TagCloudWidget)
    assert len(tag_clouds) >= 1
    # Check if 'nature' tag is visible
    assert any("nature" in lbl.text() for lbl in tag_clouds[0].findChildren(QLabel))
    
    # Verify Width uses NumericWidget
    numerics = window.metadata_panel.findChildren(NumericWidget)
    assert len(numerics) >= 2 # width and height
    assert any(n.spin.value() == 1920 for n in numerics)
    
    # Verify Name uses standard QLineEdit
    edits = window.metadata_panel.findChildren(QLineEdit)
    assert any(e.text() == "Mock Asset" for e in edits)

@pytest.mark.asyncio
async def test_metadata_save_writeback(dashboard_view, qtbot):
    """
    Scenario: User edits metadata and clicks 'Save Changes'.
    Verify: AGMMapper.save and Pyexiv2Handler.write_xmp are called.
    """
    window, vm, mock_mapper = dashboard_view
    
    # 1. Setup Mock for Pyexiv2Handler
    with patch("src.modules.assets.infrastructure.handlers.pyexiv2.Pyexiv2Handler.write_xmp", new_callable=AsyncMock) as mock_write:
        mock_write.return_value = True
        
        # 2. Select Asset to populate metadata panel
        await vm.search("forest")
        await asyncio.sleep(0.1)
        item = window.results_panel.item(0)
        rect = window.results_panel.visualItemRect(item)
        qtbot.mouseClick(window.results_panel.viewport(), Qt.LeftButton, pos=rect.center())
        
        # Wait for populating
        for _ in range(50):
            if window.metadata_panel.child_vm: break
            await asyncio.sleep(0.1)
        
        # 3. Modify a field in the ViewModel directly (simulating Auto-GUI edit)
        meta_vm = window.metadata_panel.child_vm
        meta_vm.update_property("name", "Updated Brand Name")
        meta_vm.update_property("description", "A beautiful forest photo.")
        
        # 4. Click 'Save Changes' (it's in the metadata panel, wired to MetadataViewModel.save_changes)
        save_btn = window.metadata_panel.save_btn
        qtbot.mouseClick(save_btn, Qt.LeftButton)
        
        # 5. Wait for save to complete
        for _ in range(50):
            if not save_btn.isEnabled(): # It might disable during save
                pass
            await asyncio.sleep(0.1)
            
        # 6. Verify calls
        # Note: we need to yield to the event loop for async save_changes to run
        await asyncio.sleep(0.5)
        
        # AGMMapper.save should have been called
        assert mock_mapper.save.called
        
        # Pyexiv2Handler.write_xmp should have been called with correct tags
        assert mock_write.called
        args, kwargs = mock_write.call_args
        assert "file:///test.jpg" in args[0]
        tags = args[1]
        assert tags["Xmp.dc.title"] == "Updated Brand Name"
        assert tags["Xmp.dc.description"] == "A beautiful forest photo."
