import sys
import asyncio
import pytest
import qasync
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from PySide6.QtWidgets import QApplication, QPushButton, QFileDialog
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from src.core.system import System
from src.core.module import BaseModule
from src.apps.asset_explorer.main import AssetExplorerDashboard
from src.apps.asset_explorer.module import AssetExplorerModule
from src.modules.agm.module import AGMModule
from src.modules.assets.module import AssetsModule
from src.modules.assets.domain.models import ImageAsset, Tag
from src.modules.agm.mapper import AGMMapper
from src.modules.assets.domain.services import AssetIngestionService

# 1. Custom Provider to swap real infrastructure with mocks where needed
from dishka import Provider, Scope, provide

class MockInfraProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_neo_driver(self) -> MagicMock:
        driver = MagicMock()
        session = AsyncMock()
        driver.session.return_value = session
        return driver

    @provide(scope=Scope.REQUEST)
    async def provide_ingest_service(self) -> MagicMock:
        return AsyncMock(spec=AssetIngestionService)

class TestModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.provider = MockInfraProvider()

@pytest.fixture
def qasync_app(qtbot):
    """Fixture to ensure qasync loop is active during the test."""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    yield app
    # Clean up loop
    if loop.is_running():
        loop.stop()
    if not loop.is_closed():
        loop.close()

@pytest.fixture
async def full_system():
    """Starts the full BCor system with the Asset Explorer and Assets modules."""
    system = System(modules=[
        AGMModule(), 
        AssetsModule(), 
        AssetExplorerModule(),
        TestModule()
    ])
    await system.start()
    yield system
    await system.stop()

@pytest.mark.asyncio
async def test_explorer_full_lifecycle(qasync_app, full_system, qtbot):
    """
    E2E Test Case: Full App Lifecycle
    1. Mass Ingest from real path.
    2. Dynamic Search construction.
    3. Pagination across batches.
    4. Asset selection & Meta update.
    """
    system = full_system
    real_path = r"D:\image_db\safe repo\asorted images\3"
    
    async with system.container() as scope:
        # Get ViewModel and Mapper
        from src.apps.asset_explorer.presentation.viewmodels.explorer import AssetExplorerViewModel
        vm = await scope.get(AssetExplorerViewModel)
        mapper = await scope.get(AGMMapper)
        ingest_service = await scope.get(AssetIngestionService)
        
        # Instantiate Dashboard
        window = AssetExplorerDashboard(vm)
        qtbot.addWidget(window)
        window.show()
        
        # --- SCENARIO 1: INGESTION ---
        # Mock QFileDialog to return the real path
        with patch.object(QFileDialog, 'getExistingDirectory', return_value=real_path):
            ingest_btn = window.hud.ingest_btn
            qtbot.mouseClick(ingest_btn, Qt.LeftButton)
            
            # Verify ingest_directory was called
            ingest_service.ingest_directory.assert_called_with(real_path)
            
        # --- SCENARIO 2: SEARCH DISCOVERY ---
        # Wait for search schema to load (triggered by refresh_search_schema in __init__)
        for _ in range(50):
            if window.search_panel.constructor.layout().count() > 0:
                break
            await asyncio.sleep(0.1)
            
        # Verify dynamic widgets spawned (e.g., 'Width' slider for ImageAsset)
        labels = [lbl.text() for lbl in window.search_panel.constructor.findChildren(QPushButton)]
        # We search for search button and labels in layouts
        from PySide6.QtWidgets import QLabel
        all_labels = [l.text() for l in window.search_panel.constructor.findChildren(QLabel)]
        assert any("Width" in s for s in all_labels)
        
        # --- SCENARIO 3: PAGINATION ---
        # Mock Mapper to return 501 items
        mock_results = [
            ImageAsset(id=f"img-{i}", uri=f"file:///{i}.jpg", name=f"Img {i}")
            for i in range(501)
        ]
        
        # Helper to simulate Neo4j results for the mapper
        async def mock_search_paged(*args, **kwargs):
            offset = kwargs.get('skip', 0)
            limit = kwargs.get('limit', 500)
            return mock_results[offset : offset + limit]

        # Intercept the query to inject paged data
        with patch.object(vm._mapper, 'query') as mock_query_gen:
            q_mock = MagicMock()
            q_mock.all = AsyncMock(side_effect=mock_search_paged)
            mock_query_gen.return_value = q_mock
            
            # Trigger search
            await vm.search()
            await asyncio.sleep(0.2)
            
            # Verify Page 1
            assert window.results_panel.count() == 500
            assert "Page 1" in window.pagination_bar.label.text()
            assert window.pagination_bar.next_btn.isEnabled()
            
            # Navigate to Page 2
            qtbot.mouseClick(window.pagination_bar.next_btn, Qt.LeftButton)
            await asyncio.sleep(0.2)
            
            assert window.results_panel.count() == 1
            assert "Page 2" in window.pagination_bar.label.text()
            assert not window.pagination_bar.next_btn.isEnabled()
            assert window.pagination_bar.prev_btn.isEnabled()

        # --- SCENARIO 4: METADATA & SAVE ---
        # Select the single item on page 2
        item = window.results_panel.item(0)
        rect = window.results_panel.visualItemRect(item)
        qtbot.mouseClick(window.results_panel.viewport(), Qt.LeftButton, pos=rect.center())
        
        # Wait for metadata panel
        for _ in range(50):
            if window.metadata_panel.child_vm: break
            await asyncio.sleep(0.1)
            
        # Update name
        meta_vm = window.metadata_panel.child_vm
        meta_vm.update_property("name", "E2E Final Title")
        
        # Mock Mapper.save
        mapper.save = AsyncMock(return_value=True)
        
        # Click Save
        qtbot.mouseClick(window.metadata_panel.save_btn, Qt.LeftButton)
        await asyncio.sleep(0.5)
        
        # Final Check: Mapper.save was called with the updated name
        assert mapper.save.called
        updated_asset = mapper.save.call_args[0][0]
        assert updated_asset.name == "E2E Final Title"

    print("SUCCESS: E2E Full Lifecycle Verified")
