import pytest
from src.apps.experemental.sanali.Python.core_apps.services.service_container import ServiceContainer
from src.apps.experemental.sanali.Python.core_apps.repository.annotation_repository import AnnotationRepositoryInterface
from unittest.mock import MagicMock

from src.apps.experemental.sanali.Python.core_apps.repository.annotation_repository import AnnotationRepositoryInterface
from src.core.testing import BCorTestSystem

@pytest.mark.asyncio
async def test_get_annotation_repository_from_bcor():
    """
    TDD Test: Verify that AnnotationRepository is resolved via BCor bridge.
    """
    manifest = "src/apps/experemental/sanali/Python/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
        container = get_service_container()
        await container.prepare_bcor_bridge(extra_services=[AnnotationRepositoryInterface])
        
        # Resolve repository
        repo = container.get_service(AnnotationRepositoryInterface)
        
        assert isinstance(repo, AnnotationRepositoryInterface)
        # Check for async methods in the new implementation
        assert hasattr(repo, 'get_all_annotations_async') or hasattr(repo, 'get_all_annotations')
        
        # Integration check with mock job
        job_id = "test_job_123"
        annotations = repo.get_all_annotations(job_id)
        assert isinstance(annotations, list)
