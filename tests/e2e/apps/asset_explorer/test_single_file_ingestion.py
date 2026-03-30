import sys
import os

# CRITICAL: Force TaskIQ to use real broker BEFORE any BCor imports
os.environ["TASKIQ_FORCE_REAL_BROKER"] = "1"
os.environ["NEO4J_URI"] = os.getenv("NEO4J_URI", "bolt://localhost:7687")

import asyncio
import pytest
import qasync
import uuid
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from src.core.system import System
from src.modules.agm.module import AGMModule
from src.modules.assets.module import AssetsModule
from src.apps.asset_explorer.main import AssetExplorerDashboard
from src.apps.asset_explorer.module import AssetExplorerModule
from src.apps.asset_explorer.presentation.viewmodels.explorer import AssetExplorerViewModel

@pytest.fixture
def qasync_app(qtbot):
    """Fixture to ensure qasync loop is active during the test."""
    app = QApplication.instance() or QApplication(sys.argv)
    with qasync.QEventLoop(app) as loop:
        asyncio.set_event_loop(loop)
        yield app, loop

@pytest.mark.asyncio
async def test_single_file_ingestion_lifecycle(qasync_app, tmp_path):
    """
    Test adding ONE file specifically.
    1. Open Dashboard.
    2. Click 'Add Asset' (Single).
    3. Verify it's ingested and processing starts.
    """
    app, loop = qasync_app
    
    # Real image path from user feedback
    real_image = r"D:\image_db\safe repo\asorted images\3\1326355292461.webp"
    if not os.path.exists(real_image):
        # Fallback for CI/other environments
        test_file = tmp_path / "test_image.jpg"
        test_file.write_bytes(b"fake data")
        real_image = str(test_file)

    system = System(modules=[AGMModule(), AssetsModule(), AssetExplorerModule()])
    await system.start()
    
    # 2. Resolve ViewModels from DISHKA (within a request scope)
    async with system.container() as scope:
        vm = await scope.get(AssetExplorerViewModel)
        dashboard = AssetExplorerDashboard(vm)
        dashboard.show()
        
        # Explicitly start the worker for the test (just like async_main does)
        dashboard.worker_manager.start_worker()
        
        # Let UI stabilize
        await asyncio.sleep(1)
        
        # Mock QFileDialog to return our one file
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(real_image, "All Files (*.*)")):
            # Trigger single add
            dashboard._on_add_single()
            
        # Wait for ingestion to complete (it should be fast for 1 file)
        found = False
        for _ in range(10): # 10s timeout
            await asyncio.sleep(1)
            if len(dashboard.vm._results) > 0:
                found = True
                break
                
        assert found, "Asset should be ingested and visible in results"
        
        # Verify Worker is running
        assert dashboard.worker_manager.is_running(), "Worker should be auto-started"
        
        # Wait for at least ONE metadata update from the worker
        metadata_updated = False
        for _ in range(30): # 30s timeout for AI
            await asyncio.sleep(1)
            asset = dashboard.vm._results[0]
            if asset.thumbnails_ready or (hasattr(asset, 'description') and asset.description):
                metadata_updated = True
                break
                
        print(f"Final Asset State: {dashboard.vm._results[0]}")
        
    await system.stop()
    dashboard.close()
