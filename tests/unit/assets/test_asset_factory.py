import pytest
from src.modules.assets.domain.factory import AssetFactory
from src.modules.assets.domain.models import ImageAsset, DocumentAsset

def test_asset_factory_creates_image_from_path():
    # We use a non-existent path but the factory should still create the object
    path = "test.jpg"
    asset = AssetFactory.create_from_path(path)
    
    assert isinstance(asset, ImageAsset)
    assert asset.id is not None
    assert len(asset.id) > 0
    assert asset.uri == f"file://{path}"
    assert asset.mime_type == "image/jpeg"

def test_asset_factory_creates_webp():
    asset = AssetFactory.create("file:///image.webp")
    assert asset.mime_type == "image/webp"
    assert isinstance(asset, ImageAsset)

def test_asset_factory_creates_document():
    asset = AssetFactory.create("file:///doc.pdf")
    assert asset.mime_type == "application/pdf"
    assert isinstance(asset, DocumentAsset)
