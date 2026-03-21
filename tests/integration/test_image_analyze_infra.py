import pytest
import asyncio
from pathlib import Path
from PIL import Image
from src.apps.ImageAnalyze.infrastructure.sqlite_repo import SqliteImageRepo
from src.apps.ImageAnalyze.infrastructure.image_scanner import ImageScanner

@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "test_mariner.db"
    return SqliteImageRepo(str(db_path))

@pytest.fixture
def sample_images(tmp_path):
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    
    # Create a few real images
    for i in range(3):
        img = Image.new("RGB", (100 * (i+1), 100), color="red")
        img.save(images_dir / f"image_{i}.jpg")
    
    # One png
    img = Image.new("RGBA", (50, 50), color="blue")
    img.save(images_dir / "logo.png")
    
    return images_dir

@pytest.mark.asyncio
async def test_scanner_and_repo_integration(test_db, sample_images):
    scanner = ImageScanner()
    
    # Define progress callback
    progress_calls = []
    async def progress(current, total, msg):
        progress_calls.append((current, total, msg))
        
    # Scan
    records = await scanner.scan_directory(str(sample_images), progress_callback=progress)
    
    assert len(records) == 4
    assert any(r.extension == ".png" for r in records)
    assert len(progress_calls) > 0
    
    # Insert to DB
    test_db.bulk_insert(records)
    
    # Verify DB
    stats = test_db.get_stats()
    assert stats["total_images"] == 4
    assert stats["formats"][".jpg"] == 3
    assert stats["formats"][".png"] == 1
    
    all_records = test_db.get_all()
    assert len(all_records) == 4
    for r in all_records:
        assert Path(r.path).exists()
        assert r.width > 0
        assert r.height > 0
