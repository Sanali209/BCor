import pytest
import os
from pathlib import Path
from src.core.system import System
from src.apps.experemental.imgededupe.settings import ImageDedupeSettings

@pytest.mark.asyncio
async def test_imgededupe_bootstrap():
    manifest_path = Path(__file__).parent.parent.parent.parent / "src" / "apps" / "experemental" / "imgededupe" / "app.toml"
    assert manifest_path.exists()
    
    system = System.from_manifest(str(manifest_path))
    await system.start()
    
    async with system.container() as request_container:
        settings = await request_container.get(ImageDedupeSettings)
        assert settings.db_path == "dedup_app.db"
        assert "phash" in settings.enabled_engines
    
    await system.stop()
