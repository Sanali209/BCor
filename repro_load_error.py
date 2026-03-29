
import asyncio
from typing import Any
from adaptix import Retort
from dishka import make_async_container, Provider, Scope, provide
from src.modules.agm.mapper import AGMMapper
from src.modules.assets.domain.models import ImageAsset
from src.core.messagebus import MessageBus

class MockUoW:
    def _commit(self): pass
    def rollback(self): pass
    def _get_all_seen_aggregates(self): return []

class AppProvider(Provider):
    @provide(scope=Scope.APP)
    def get_bus(self) -> MessageBus:
        return MessageBus(uow=MockUoW())

async def reproduce():
    container = make_async_container(AppProvider())
    bus = await container.get(MessageBus)
    mapper = AGMMapper(container=container, message_bus=bus)
    
    # Mock record from Neo4j with potential issues
    record = {
        "id": "test-id",
        "uri": "file:///test.jpg",
        "name": "test.jpg",
        "mime_type": "image/jpeg",
        "description": "test image",
        "content_hash": "hash123",
        "size": 1024,
        "width": 800,
        "height": 600,
        "clip_embedding": "invalid-json", # Should fail or be handled
        "blip_embedding": None, # Potential failure
        "thumbnail_bytes": "not-bytes-but-string", # Common failure point
        "perceptual_hash": "hash",
        "exif_data": "{}",
        "labels": ["ImageAsset"]
    }
    
    await mapper.register_subclass("ImageAsset", ImageAsset)
    
    print("Attempting to load ImageAsset...")
    try:
        asset = await mapper.load(ImageAsset, record)
        print(f"Successfully loaded: {asset.id}")
    except Exception as e:
        print(f"FAILED to load: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reproduce())
