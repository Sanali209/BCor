import pytest
from unittest.mock import MagicMock, AsyncMock
from src.apps.experemental.declarative_imgededupe.triage import (
    CommandHistory, 
    DeleteAssetCommand, 
    AnnotateRelationCommand
)
from src.modules.assets.domain.models import ImageAsset, RelationType

@pytest.fixture
def mock_mapper():
    m = MagicMock()
    m.save = AsyncMock()
    m.delete = AsyncMock()
    return m

@pytest.fixture
def sample_asset():
    return ImageAsset(id="a1", uri="file://1.jpg", name="1", mime_type="image/jpeg", description="", content_hash="h1")

@pytest.mark.timeout(30)
@pytest.mark.asyncio
async def test_delete_command_executes_and_undoes(mock_mapper, sample_asset):
    """DeleteAssetCommand should call mapper.delete and then mapper.save (undo)."""
    cmd = DeleteAssetCommand(mapper=mock_mapper, asset=sample_asset)
    
    # Execute
    await cmd.execute()
    mock_mapper.delete.assert_called_once_with(sample_asset)
    
    # Undo
    await cmd.undo()
    mock_mapper.save.assert_called_once_with(sample_asset)

@pytest.mark.timeout(30)
@pytest.mark.asyncio
async def test_annotate_command_updates_relation(mock_mapper, sample_asset):
    """AnnotateRelationCommand should update the relation_type in the graph."""
    # We assume 'target_id' is the other asset
    cmd = AnnotateRelationCommand(
        mapper=mock_mapper, 
        asset=sample_asset, 
        target_id="a2", 
        new_relation=RelationType.DUPLICATE
    )
    
    await cmd.execute()
    # Check if 'similar' relationship was updated
    found = False
    for sim in sample_asset.similar:
        if sim.id == "a2":
            assert sim.relation_type == RelationType.DUPLICATE
            found = True
    assert found
    mock_mapper.save.assert_called()

@pytest.mark.timeout(30)
@pytest.mark.asyncio
async def test_command_history_pushes_and_undoes():
    """CommandHistory should manage the undo stack."""
    history = CommandHistory()
    cmd1 = MagicMock()
    cmd1.undo = AsyncMock()
    cmd2 = MagicMock()
    cmd2.undo = AsyncMock()
    
    history.push(cmd1)
    history.push(cmd2)
    
    await history.undo()
    cmd2.undo.assert_called_once()
    cmd1.undo.assert_not_called()
    
    await history.undo()
    cmd1.undo.assert_called_once()
