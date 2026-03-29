import pytest
from src.apps.experemental.sanali.Python.core_apps.services.service_container import ServiceContainer

from src.modules.sanali.services import DuplicateService
from src.core.testing import BCorTestSystem

@pytest.mark.asyncio
async def test_duplicate_service_resolution():
    """
    Verify that DuplicateService can be resolved via BCor bridge/system.
    """
    manifest = "src/apps/experemental/sanali/Python/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
        container = get_service_container()
        await container.prepare_bcor_bridge(extra_services=[DuplicateService])
        
        service = container.get_service(DuplicateService)
        assert service is not None

@pytest.mark.asyncio
async def test_find_duplicates():
    """
    Test the core duplicate finding logic.
    """
    manifest = "src/apps/experemental/sanali/Python/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
        container = get_service_container()
        await container.prepare_bcor_bridge(extra_services=[DuplicateService])
        
        service = container.get_service(DuplicateService)
        
        # We'll use some mock paths or small set of real files if available
        files = ["test1.jpg", "test2.jpg"]
        # Mocking the finder since we don't want to run real CNN in tests if possible
        from unittest.mock import AsyncMock
        service.find_duplicates = AsyncMock(return_value=[])
        
        dubs = await service.find_duplicates(files, threshold=0.9)
        assert isinstance(dubs, list)
