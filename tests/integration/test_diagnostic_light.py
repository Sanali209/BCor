"""LIGHTWEIGHT DIAGNOSTIC: 10x Core Pipeline Verification."""
import asyncio
import os
import sys
import uuid
from typing import Any

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from neo4j import AsyncGraphDatabase
from dishka import make_async_container, Provider, provide, Scope
from loguru import logger

from src.core.messagebus import MessageBus
from src.core.unit_of_work import AbstractUnitOfWork
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.handlers import handle_stored_field_recalc
from src.modules.agm.messages import StoredFieldRecalculationRequested
from src.modules.assets.domain.factory import AssetFactory
from src.modules.assets.infrastructure.providers import AssetsInfrastructureProvider
from src.modules.assets.domain.models import ImageAsset
from src.adapters.taskiq_broker import broker

# --- DI Mocks ---
class _MockUoW(AbstractUnitOfWork):
    def _commit(self): pass
    def rollback(self): pass
    def _get_all_seen_aggregates(self): return []

class _AppProvider(Provider):
    @provide(scope=Scope.APP)
    def get_uow(self) -> AbstractUnitOfWork: return _MockUoW()
    @provide(scope=Scope.APP)
    def get_bus(self, uow: AbstractUnitOfWork) -> MessageBus: return MessageBus(uow=uow)
    @provide(scope=Scope.APP)
    def get_registry(self) -> Any: return AssetsInfrastructureProvider().provide_handler_registry()

async def main():
    IMG_PATH = r"D:\image_db\safe repo\ddsearch\kim_possible\kim_possible_1.webp"
    NEO4J_URI = "bolt://127.0.0.1:7687"
    AUTH = ("neo4j", "password")

    print(f"\n🚀 STARTING LIGHT DIAGNOSTIC VERIFICATION on {os.path.basename(IMG_PATH)}")
    await broker.startup()
    
    try:
        container = make_async_container(_AppProvider(), AssetsInfrastructureProvider())
        bus = await container.get(MessageBus)
        bus.register_event(StoredFieldRecalculationRequested, handle_stored_field_recalc)
        
        mapper = AGMMapper(container=container, message_bus=bus)
        factory = AssetFactory()

        async with AsyncGraphDatabase.driver(NEO4J_URI, auth=AUTH) as driver:
            node_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"file://{IMG_PATH}"))
            
            # 1. Clear State
            async with driver.session() as s:
                await s.run("MATCH (n {id: $id}) DETACH DELETE n", id=node_id)
            print("    [1] Clean: DB Reset for target node.")

            # 2. Ingest
            asset = factory.create_from_path(IMG_PATH)
            async with driver.session() as s:
                await mapper.save(asset, session=s)
            print("    [2] Ingest: Initial save (Triggers dispatched).")

            # 3. Poll Core 10x Fields
            fields_to_check = {
                "perceptual_hash": "perceptual_hash",
                "exif_data": "exif_data",
                "xmp_data": "xmp_data",
                "auto_tags": "auto_tags",
                "xmp_sync": "xmp_sync",
                "thumbnail_bytes": "thumbnail_bytes"
            }

            print(f"\n[3] Polling for {len(fields_to_check)} core fields...")
            for i in range(40):
                await asyncio.sleep(2)
                async with driver.session() as s:
                    r = await s.run(
                        "MATCH (n:Asset:ImageAsset {id: $id}) RETURN n, labels(n) as labels", id=node_id
                    )
                    record = await r.single()
                    if not record: continue
                    n = record["n"]
                    labels = record["labels"]
                    
                    found = [f for f in fields_to_check if n.get(f) is not None and (not isinstance(n.get(f), (list, dict, bytes)) or len(n.get(f)) > 0 or n.get(f) is True)]
                    missing = [f for f in fields_to_check if f not in found]
                    
                    if i % 5 == 0 or not missing:
                        print(f"    [{i*2}s] Status: Found {len(found)}/{len(fields_to_check)} CORE fields. Missing: {missing}")
                    
                    if not missing:
                        print("\n✅ CORE SUCCESS: Metadata Evolution Verified!")
                        print(f"      Labels    : {labels}")
                        print(f"      XMP/Auto-Tags: {n.get('auto_tags')}")
                        return

            print("\n❌ DIAGNOSTIC TIMEOUT: Core fields or Inheritance labels missing.")
    finally:
        await broker.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
