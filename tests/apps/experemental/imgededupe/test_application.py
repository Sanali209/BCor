import pytest
import os
from PIL import Image
from src.core.system import System
from src.apps.experemental.imgededupe.core.domain.messages import StartScanCommand, ScanFinishedEvent

@pytest.fixture
def test_image(tmp_path):
    img_path = tmp_path / "test.jpg"
    img = Image.new('RGB', (100, 100), color=(73, 109, 137))
    img.save(img_path)
    return str(img_path)

@pytest.fixture
def app_toml(tmp_path):
    toml_path = tmp_path / "app.toml"
    with open(toml_path, "w") as f:
        f.write('[modules]\nenabled = ["imgededupe"]\npaths = ["src/apps/experemental"]\n')
    return str(toml_path)

@pytest.mark.asyncio
async def test_start_scan_integration(test_image, app_toml, tmp_path):
    # Update settings to use a temporary DB
    db_path = str(tmp_path / "integration.db")
    
    # We can override settings by creating a system and then accessing the container
    system = System.from_manifest(app_toml)
    async with system:
        # Override settings in container if possible, 
        # but for this test we'll just check if it runs with defaults or provided path
        # Actually, let's just use the command
        
        # Subscribe to finish event to verify it completes
        finished = asyncio.Event()
        
        async def on_finished(event: ScanFinishedEvent):
            finished.set()
        
        system.message_bus.subscribe(ScanFinishedEvent, on_finished)
        
        command = StartScanCommand(scan_roots=[os.path.dirname(test_image)])
        await system.message_bus.handle(command)
        
        # Wait with timeout
        import asyncio
        try:
            await asyncio.wait_for(finished.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            pytest.fail("Scan finished event not received")

        # Actually, let's verify if 'integration.db' exists if we can inject it.

@pytest.mark.asyncio
async def test_duplicate_detection_integration(tmp_path, app_toml):
    # Create two identical images
    img1_path = tmp_path / "img1.jpg"
    img2_path = tmp_path / "img2.jpg"
    img3_path = tmp_path / "unique.jpg"
    
    img = Image.new('RGB', (100, 100), color=(73, 109, 137))
    img.save(img1_path)
    img.save(img2_path)
    
    img_unique = Image.new('RGB', (100, 100), color=(255, 0, 0))
    img_unique.save(img3_path)
    
    system = System.from_manifest(app_toml)
    async with system:
        import asyncio
        finished = asyncio.Event()
        results = {}

        async def on_finished(event: ScanFinishedEvent):
            results['total'] = event.total_processed
            results['duplicates'] = event.duplicates_found
            finished.set()
        
        system.message_bus.subscribe(ScanFinishedEvent, on_finished)
        
        command = StartScanCommand(
            scan_roots=[str(tmp_path)],
            threshold=2
        )
        await system.message_bus.handle(command)
        
        await asyncio.wait_for(finished.wait(), timeout=10.0)

        assert results['total'] == 3
        # Depending on how the loop ran, img1 and img2 should be detected as duplicates
        assert results['duplicates'] >= 1
