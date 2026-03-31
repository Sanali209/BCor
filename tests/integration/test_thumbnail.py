import asyncio
import pathlib
import os
from src.modules.assets.infrastructure.handlers.thumbnail import ThumbnailHandler

async def test_thumbnail_handler():
    """TDD Step 3: Verify ThumbnailHandler success path."""
    # Create a dummy image
    from PIL import Image
    test_img = pathlib.Path("test_input.png")
    Image.new("RGB", (1000, 1000), color="red").save(test_img)
    
    try:
        uri = f"file:///{test_img.absolute()}"
        ctx = {
            "content_hash": "abcdef1234567890",
            "mime_type": "image/png",
            "storage_root": "test_data"
        }
        
        print(f"Running ThumbnailHandler for {uri}...")
        success = await ThumbnailHandler.run(uri, context=ctx)
        print(f"Result: {success}")
        
        # Check if files exist
        for size in ["small", "medium", "large"]:
            # Construction logic from get_cas_path: test_data/thumbs/ab/cd/abcdef1234567890_{size}.png
            p = pathlib.Path("test_data/thumbs/ab/cd/abcdef1234567890_" + size + ".png")
            print(f"Checking {p}: {p.exists()}")
            assert p.exists()

    finally:
        if test_img.exists(): test_img.unlink()
        import shutil
        if pathlib.Path("test_data").exists():
            shutil.rmtree("test_data")

if __name__ == "__main__":
    asyncio.run(test_thumbnail_handler())
