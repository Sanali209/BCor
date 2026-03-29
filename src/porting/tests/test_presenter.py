import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
import os
from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
from src.modules.sanali.presenters import ImageDedupPresenter
from src.modules.sanali.domain import ProjectImageItem, ProjectImageGroup
from src.modules.sanali.services import ProjectStateService, NeiroFilterService, UserPreferenceService

from src.core.testing import BCorTestSystem

@pytest.mark.asyncio
async def test_presenter_advision_flow():
    """
    Verify that DedupPresenter coordinates Advision list creation.
    """
    manifest = "src/apps/experemental/sanali/Python/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        presenter = await system.container.get(ImageDedupPresenter)
        
        # Mock initial state
        img = ProjectImageItem(path="query.jpg")
        presenter.state_service.groups = [ProjectImageGroup(label="Init", items=[img])]
        
        # Mock similar images finding
        similar = [ProjectImageItem(path=f"sim{i}.jpg") for i in range(5)]
        presenter.dup_service.find_similar = AsyncMock(return_value=similar)
        
        # Run Advision creation
        await presenter.create_advision_list()
        
        # Verify
        groups = presenter.get_groups()
        assert len(groups) == 1
        assert groups[0].label == "query.jpg"
        assert len(groups[0].items) == 6 # 1 original + 5 similar
        assert groups[0].items[0].path == "query.jpg"

@pytest.mark.asyncio
async def test_presenter_neiro_filter_flow():
    """
    Verify that DedupPresenter coordinates NeiroFilter tagging.
    """
    manifest = "src/apps/experemental/sanali/Python/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        presenter = await system.container.get(ImageDedupPresenter)
        
        # Mock initial images
        images = [ProjectImageItem(path="i1.jpg"), ProjectImageItem(path="i2.jpg")]
        presenter.state_service.groups = [ProjectImageGroup(label="Init", items=images)]
        
        # Mock tagging results
        tagged = {
            "cat": ["i1.jpg"],
            "dog": ["i2.jpg"]
        }
        presenter.neiro_service.tag_images = AsyncMock(return_value=tagged)
        
        # Run NeiroFilter
        await presenter.create_neiro_filter_list(model="test-model")
        
        # Verify
        groups = presenter.get_groups()
        assert len(groups) == 2
        labels = [g.label for g in groups]
        assert "cat" in labels
        assert "dog" in labels
        presenter.neiro_service.tag_images.assert_called_once()

@pytest.mark.asyncio
async def test_user_preference_service():
    """
    Verify UserPreferenceService (diskcache based).
    """
    manifest = "src/apps/experemental/sanali/Python/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        pref_service = await system.container.get(UserPreferenceService)
        
        # For now, just test basic add/get
        pref_service.add_hidden_pair("p1", "p2")
        pairs = pref_service.get_hidden_pairs()
        
        from src.common.paths import PathNormalizer
        p1_abs = PathNormalizer.norm("p1")
        p2_abs = PathNormalizer.norm("p2")
        expected_pair = tuple(sorted([p1_abs, p2_abs]))
        
        assert expected_pair in pairs
        
        pref_service.add_imageset_folder("/path/to/set")
        sets = pref_service.get_imageset_folders()
        
        expected_set = PathNormalizer.norm("/path/to/set")
        assert expected_set in sets
