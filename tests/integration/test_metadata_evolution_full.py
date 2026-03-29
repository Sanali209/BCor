"""Comprehensive verification for 10x Metadata Evolution (XMP, Inheritance, Dependencies)."""
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
    NEO4J_URI = "bolt://localhost:7687"
    AUTH = ("neo4j", "password")

    print(f"\n[1] Setup: Metadata Evolution Test on {os.path.basename(IMG_PATH)}")
    
    # 0. Start TaskIQ Broker
    await broker.startup()
    
    try:
        container = make_async_container(_AppProvider(), AssetsInfrastructureProvider())
        bus = await container.get(MessageBus)
        bus.register_event(StoredFieldRecalculationRequested, handle_stored_field_recalc)
        
        mapper = AGMMapper(container=container, message_bus=bus)
        factory = AssetFactory()

        async with AsyncGraphDatabase.driver(NEO4J_URI, auth=AUTH) as driver:
            node_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"file://{IMG_PATH}"))
            
            # 1. Clean up
            async with driver.session() as s:
                await s.run("MATCH (n {id: $id}) DETACH DELETE n", id=node_id)
            print(f"    Node {node_id} cleared.")

            # 2. Ingest
            asset = factory.create_from_path(IMG_PATH)
            # Ensure it's an ImageAsset
            assert isinstance(asset, ImageAsset)
            
            async with driver.session() as s:
                # First save: triggers base metadata (EXIF, XMP, pHash)
                await mapper.save(asset, session=s)
            
            print("    Phase 1: Ingestion completed. Base tasks dispatched.")

            # 3. Poll for Evolution Results
            # We expect: 
            #  - [:Asset:ImageAsset] labels
            #  - exif_data, xmp_data (processed by pyexiv2)
            #  - auto_tags (depends on exif/xmp)
            #  - xmp_sync (depends on auto_tags)
            fields_to_check = [
                "exif_data", "xmp_data", "perceptual_hash", 
                "auto_tags", "xmp_sync"
            ]
            
            print("\n[2] Polling for multi-label and cascading metadata...")
            for i in range(60):
                await asyncio.sleep(2)
                async with driver.session() as s:
                    # Check for MULTIPLE LABELS explicitly
                    r = await s.run(
                        "MATCH (n:Asset:ImageAsset {id: $id}) RETURN n, labels(n) as labels", 
                        id=node_id
                    )
                    record = await r.single()
                    if not record:
                        print(f"    [{i*2}s] Node with correct labels not found yet...")
                        continue
                    
                    n = record["n"]
                    labels = record["labels"]
                    
                    found = []
                    missing = []
                    for f in fields_to_check:
                        val = n.get(f)
                        if val is not None and (not isinstance(val, (list, dict)) or len(val) > 0 or val is True):
                            found.append(f)
                        else:
                            missing.append(f)
                    
                    if i % 5 == 0 or not missing:
                        print(f"    [{i*2}s] Labels={labels} | Found={found} | Missing={missing}")

                    if not missing:
                        print("\n✅ SUCCESS: 10x Metadata Evolution Verified!")
                        print(f"      Labels    : {labels}")
                        print(f"      EXIF Keys : {len(n.get('exif_data', {}))}")
                        print(f"      XMP Keys  : {len(n.get('xmp_data', {}))}")
                        print(f"      Sync Status: {n.get('xmp_sync')}")
                        
                        # Verify physical write-back if possible (via another read)
                        # We trust the Pyexiv2Handler.write_xmp logic from the scratch script
                        return

            print("\n❌ TIMEOUT: Evolution failed to complete.")

    finally:
        await broker.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
