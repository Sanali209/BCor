import pytest
from src.apps.experemental.sanali.Python.core_apps.services.service_container import ServiceContainer
# We will define this class in the implementation
# from src.modules.sanali.use_cases import ImageManagementUseCase

from src.modules.sanali.use_cases import ImageManagementUseCase
from src.core.testing import BCorTestSystem

@pytest.mark.asyncio
async def test_image_management_use_case_resolution():
    """
    Verify that ImageManagementUseCase can be resolved via BCor bridge/system.
    """
    manifest = "src/apps/experemental/sanali/Python/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
        container = get_service_container()
        await container.prepare_bcor_bridge(extra_services=[ImageManagementUseCase])
        
        use_case = container.get_service(ImageManagementUseCase)
        assert use_case is not None

@pytest.mark.asyncio
async def test_mark_as_imageset():
    """
    Test the business logic for marking a folder as an imageset.
    """
    manifest = "src/apps/experemental/sanali/Python/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
        container = get_service_container()
        await container.prepare_bcor_bridge(extra_services=[ImageManagementUseCase])
        
        use_case = container.get_service(ImageManagementUseCase)
        
        test_path = "D:/test/imageset"
        use_case.mark_directory_as_imageset(test_path)
        
        imagesets = use_case.get_imagesets()
        from src.common.paths import PathNormalizer
        assert PathNormalizer.norm(test_path) in imagesets
