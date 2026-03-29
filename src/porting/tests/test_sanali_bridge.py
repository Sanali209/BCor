import pytest
from src.core.testing import BCorTestSystem
from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
from src.modules.sanali.services import ProjectStateService

@pytest.mark.asyncio
async def test_bridge_resolves_from_bcor_integration():
    """
    Integration Test: Verify that ServiceContainer can resolve 
    a real BCor service via the bridge.
    """
    manifest = "src/apps/experemental/sanali/Python/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        container = get_service_container()
        # Pre-resolve to bridge
        await container.prepare_bcor_bridge(extra_services=[ProjectStateService])
        
        # Act
        service = container.get_service(ProjectStateService)
        
        # Assert
        assert service is not None
        assert isinstance(service, ProjectStateService)
