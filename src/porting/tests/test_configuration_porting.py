import pytest
from src.apps.experemental.sanali.Python.core_apps.services.service_container import ServiceContainer
from src.apps.experemental.sanali.Python.core_apps.services.configuration_service import ConfigurationService

from src.apps.experemental.sanali.Python.core_apps.services.configuration_service import ConfigurationService
from src.core.testing import BCorTestSystem

@pytest.mark.asyncio
async def test_get_configuration_service_from_bcor():
    """
    TDD Test: Verify that ConfigurationService is resolved via BCor bridge.
    """
    manifest = "src/apps/experemental/sanali/Python/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
        container = get_service_container()
        # Pre-resolve for bridge
        await container.prepare_bcor_bridge(extra_services=[ConfigurationService])
        
        service = container.get_service(ConfigurationService)
        assert isinstance(service, ConfigurationService)
        # We can also check some values from config
        assert hasattr(service, 'get_choices_list')
