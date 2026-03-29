import pytest
from unittest.mock import AsyncMock, MagicMock
from src.apps.asset_explorer.presentation.viewmodels.explorer import AssetExplorerViewModel
from src.apps.asset_explorer.presentation.viewmodels.metadata import MetadataViewModel
from src.modules.assets.domain.models import ImageAsset

@pytest.mark.asyncio
async def test_explorer_vm_search():
    # Mock Mapper and Query
    mock_mapper = MagicMock()
    mock_query = MagicMock()
    mock_mapper.query.return_value = mock_query
    
    # Mock search results
    asset1 = ImageAsset(id="1", uri="file://1.jpg", name="Img 1")
    asset2 = ImageAsset(id="2", uri="file://2.jpg", name="Img 2")
    
    # CypherQuery.run() is async
    mock_query.run = AsyncMock(return_value=[asset1, asset2])
    
    vm = AssetExplorerViewModel(mapper=mock_mapper)
    
    # Trigger search
    await vm.search("forest")
    
    assert len(vm.results) == 2
    assert vm.results[0].id == "1"
    assert vm.results[1].id == "2"

@pytest.mark.asyncio
async def test_explorer_vm_selection():
    asset = ImageAsset(id="123", uri="file://test.jpg")
    mock_mapper = MagicMock()
    
    vm = AssetExplorerViewModel(mapper=mock_mapper)
    vm._results = [asset] # Manually seed for test
    
    assert vm.current_metadata is None
    
    # Select asset
    vm.select_asset("123")
    
    assert vm.selected_asset == asset
    assert isinstance(vm.current_metadata, MetadataViewModel)
    assert vm.current_metadata._asset == asset
