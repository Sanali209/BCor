import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from src.modules.assets.infrastructure.handlers.phash import PHashHandler
from src.modules.assets.infrastructure.handlers.clip import CLIPHandler
from src.modules.assets.infrastructure.handlers.blip import BLIPHandler
import pathlib
from PIL import Image

@pytest.fixture
def sample_image(tmp_path):
    img_path = tmp_path / "test.jpg"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path)
    return str(img_path)

@pytest.mark.timeout(30)
@pytest.mark.asyncio
async def test_phash_handler(sample_image):
    phash = await PHashHandler.run(f"file://{sample_image}")
    assert isinstance(phash, str)
    assert len(phash) > 0

@pytest.mark.timeout(30)
@pytest.mark.asyncio
async def test_clip_handler(sample_image):
    mock_model = MagicMock()
    # CLIP model.encode returns a numpy array
    mock_model.encode.return_value = np.random.rand(512).astype(np.float32)
    
    with patch("src.modules.assets.infrastructure.handlers.clip.CLIPHandler._get_model", return_value=mock_model):
        embedding = await CLIPHandler.run(f"file://{sample_image}")
        assert isinstance(embedding, list)
        assert len(embedding) == 512
        assert all(isinstance(x, float) for x in embedding)
        mock_model.encode.assert_called_once()

@pytest.mark.timeout(30)
@pytest.mark.asyncio
async def test_blip_handler(sample_image):
    mock_processor = MagicMock()
    mock_model = MagicMock()
    
    # Mock return value of model.get_image_features (torch tensor)
    import torch
    mock_output = torch.randn(1, 768)
    mock_model.get_image_features.return_value = mock_output
    
    with patch("src.modules.assets.infrastructure.handlers.blip.BLIPHandler._get_model", return_value=(mock_processor, mock_model)):
        embedding = await BLIPHandler.run(f"file://{sample_image}")
        assert isinstance(embedding, list)
        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)
        mock_model.get_image_features.assert_called_once()
