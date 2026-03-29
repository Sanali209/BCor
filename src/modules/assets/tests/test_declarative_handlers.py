import os
import pathlib
import pytest
import piexif
from typing import Annotated, Any
from dataclasses import dataclass, field

from src.modules.agm.metadata import Stored
from src.modules.assets.infrastructure.handlers.exif import PiexifHandler
from src.modules.assets.infrastructure.registry import HandlerRegistry

@pytest.mark.asyncio
async def test_piexif_handler_unicode_path(tmp_path):
    """Verify that PiexifHandler handles Russian/Unicode paths correctly on Windows."""
    # 1. Create a dummy file with Russian characters in the name
    russian_name = "тестовое_изображение.jpg"
    img_path = tmp_path / russian_name
    img_path.write_bytes(b"dummy_exif_data")

    # 2. Mock piexif.load and run the handler
    import unittest.mock as mock
    with mock.patch("piexif.load") as mock_load:
        # Mock what _sanitize_exif expects
        mock_load.return_value = {
            "0th": {piexif.ImageIFD.Make: b"Canon"},
            "Exif": {piexif.ExifIFD.DateTimeOriginal: b"2026:03:26 13:00:00"}
        }
        
        uri = str(img_path)
        result = await PiexifHandler.run(uri)
    
    # 3. Assertions
    assert result["Make"] == "Canon"
    assert result["DateTimeOriginal"] == "2026:03:26 13:00:00"
    print(f"\nSuccessfully verified Unicode path handling for: {russian_name}")

@pytest.mark.asyncio
async def test_handler_registry_named_resolution():
    """Verify that HandlerRegistry prioritizes named handlers."""
    registry = HandlerRegistry()
    
    class MockNamedHandler: pass
    class MockMimeHandler: pass
    
    registry.register("image/*", MockMimeHandler)
    registry.register_named("SpecialPiexif", MockNamedHandler)
    
    # Resolution by name should win
    resolved = registry.resolve("image/jpeg", handler_name="SpecialPiexif")
    assert resolved == MockNamedHandler
    
    # Resolution by MIME only
    resolved = registry.resolve("image/jpeg")
    assert resolved == MockMimeHandler
