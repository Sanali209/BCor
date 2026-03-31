import pytest
import asyncio
import os
import shutil
import time
from pathlib import Path
from PIL import Image, ImageDraw
from PySide6.QtCore import Qt
from qasync import QEventLoop
import qasync
from src.core.system import System
from src.apps.experemental.imgededupe.module import ImgeDeduplicationModule
from src.apps.experemental.imgededupe.ui.mainwindow import MainWindow
from src.apps.experemental.imgededupe.ui.adapter import GuiEventAdapter
from src.apps.experemental.imgededupe.core.scan_session import ScanSession
from src.apps.experemental.imgededupe.core.repositories.file_repository import FileRepository
from src.apps.experemental.imgededupe.core.repositories.cluster_repository import ClusterRepository
from src.apps.experemental.imgededupe.core.database import DatabaseManager
from src.core.messagebus import MessageBus

def create_test_image(path, color, text):
    img = Image.new('RGB', (100, 100), color=color)
    d = ImageDraw.Draw(img)
    d.text((10, 10), text, fill=(255, 255, 255))
    img.save(path)

@pytest.fixture
def test_data(tmp_path):
    """Creates a temporary directory with test images."""
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    
    # 1. Exact duplicates
    create_test_image(img_dir / "img1.png", (255, 0, 0), "RED")
    create_test_image(img_dir / "img1_dup.png", (255, 0, 0), "RED")
    
    # 2. Similar images (pHash should find them)
    create_test_image(img_dir / "img2.png", (0, 255, 0), "GREEN")
    img2_sim = Image.new('RGB', (100, 100), color=(0, 255, 0))
    d = ImageDraw.Draw(img2_sim)
    d.text((10, 10), "GREEN", fill=(255, 255, 255))
    img2_sim.putpixel((0,0), (0,0,0)) 
    img2_sim.save(img_dir / "img2_sim.png")
    
    # 3. Unique image
    create_test_image(img_dir / "unique.png", (0, 0, 255), "BLUE")
    
    return str(img_dir)

from src.porting.testing_utils import BCorTestSystem
from src.porting.porting import WindowsLoopManager

def test_complete_e2e_flow(qtbot, qapp, test_data, tmp_path):
    """
    Combined stable E2E test covering Scan, Results, and Clusters.
    """
    db_path = str(tmp_path / "test_e2e_final.db")
    manifest_path = "app.toml" # Simulated manifest or use manual setup
    
    WindowsLoopManager.setup_loop()
    loop = QEventLoop(qapp)
    asyncio.set_event_loop(loop)
    
    async def run_e2e():
        # Setup module with test config
        module = ImgeDeduplicationModule()
        # Instead of manifest, we can use manual module setup or a temp manifest
        # For simplicity, let's keep the manual System setup but wrap it in a pseudo-context 
        # or just use the system.stop() / drain logic from the kit.
        
        system = System(modules=[module], config={"imgededuplication": {"db_path": db_path}})
        await system.start()
    
        try:
            container = system.container
            bus = await container.get(MessageBus)
            adapter = await container.get(GuiEventAdapter)
            session = await container.get(ScanSession)
            file_repo = await container.get(FileRepository)
            cluster_repo = await container.get(ClusterRepository)
            db_manager = await container.get(DatabaseManager)
    
            window = MainWindow(session, file_repo, cluster_repo, db_manager, adapter, bus)
            qtbot.addWidget(window)
            window.show()
    
            # --- 1. SETUP ---
            setup = window.setup_widget
            setup.path_list.addItem(test_data)
            window.session.roots = [test_data]
            window.session.threshold = 5.0
            
            # --- 2. SCAN ---
            qtbot.mouseClick(setup.btn_start, Qt.LeftButton)
            
            # wait for results view
            timeout = time.time() + 40
            while window.stack.currentIndex() != 2:
                if time.time() > timeout:
                    pytest.fail("Timed out waiting for Results view")
                await asyncio.sleep(0.5)
            
            results_widget = window.results_widget
            assert len(results_widget.pairs) >= 2
            
            # --- 4. CLUSTERS ---
            window.act_cluster_view.trigger()
            assert window.stack.currentIndex() == 3
            
            cluster_widget = window.cluster_widget
            cluster_widget.btn_detect.click()
            
            await asyncio.sleep(1.0) # UI update
            assert cluster_widget.cluster_list.count() >= 2
            
            # Select first cluster and check contents
            cluster_widget.cluster_list.setCurrentRow(0)
            await asyncio.sleep(0.5)
            assert cluster_widget.image_list.count() >= 2
            
        finally:
            await system.stop()
            await WindowsLoopManager.drain_loop()
            window.close()

    loop.run_until_complete(run_e2e())
