import pytest
from src.apps.experemental.sanali.Python.core_apps.services.service_container import ServiceContainer

from src.modules.sanali.services import ProjectStateService
from src.modules.sanali.domain import ProjectImageGroup, ProjectImageItem
from src.core.testing import BCorTestSystem

@pytest.mark.asyncio
async def test_project_state_service_resolution():
    """
    Verify that ProjectStateService can be resolved via BCor bridge/system.
    """
    manifest = "src/apps/experemental/sanali/Python/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
        container = get_service_container()
        await container.prepare_bcor_bridge(extra_services=[ProjectStateService])
        
        service = container.get_service(ProjectStateService)
        assert service is not None

@pytest.mark.asyncio
async def test_project_state_management():
    """
    Test adding and retrieving groups from the state service.
    """
    manifest = "src/apps/experemental/sanali/Python/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
        container = get_service_container()
        await container.prepare_bcor_bridge(extra_services=[ProjectStateService])
        
        service = container.get_service(ProjectStateService)
        
        group = ProjectImageGroup(label="Group 1")
        group.items.append(ProjectImageItem(path="img1.jpg"))
        
        service.add_group(group)
        
        groups = service.get_groups()
        assert len(groups) == 1
        assert groups[0].label == "Group 1"
