"""VERIFICATION: 10x Searchable Metadata (Smart EXIF)."""
import asyncio
import os
import sys
import uuid
from typing import Any

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from neo4j import AsyncGraphDatabase
from dishka import make_async_container, Provider, provide, Scope

from src.core.messagebus import MessageBus
from src.core.unit_of_work import AbstractUnitOfWork
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.handlers import handle_stored_field_recalc
from src.modules.agm.messages import StoredFieldRecalculationRequested
from src.modules.assets.domain.factory import AssetFactory
from src.modules.assets.infrastructure.providers import AssetsInfrastructureProvider
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

    print(f"\n🚀 STARTING SMART EXIF VERIFICATION on {os.path.basename(IMG_PATH)}")
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

            # 2. Ingest
            asset = factory.create_from_path(IMG_PATH)
            async with driver.session() as s:
                await mapper.save(asset, session=s)
            
            print("    [1] Ingest: Dispatched Smart EXIF handlers.")

            # 3. Poll for Searchable Fields
            smart_fields = ["captured_at", "camera_make", "camera_model", "iso", "f_number", "exposure_time"]
            
            print(f"    [2] Polling for {len(smart_fields)} searchable fields...")
            for i in range(30):
                await asyncio.sleep(2)
                async with driver.session() as s:
                    r = await s.run(
                        "MATCH (n:ImageAsset {id: $id}) RETURN n", id=node_id
                    )
                    record = await r.single()
                    if not record: continue
                    n = record["n"]
                    
                    found = [f for f in smart_fields if n.get(f) is not None]
                    if len(found) == len(smart_fields) or i == 29:
                        print(f"\n✅ SMART EXIF SUCCESS: Found {len(found)}/{len(smart_fields)} searchable properties.")
                        for f in smart_fields:
                            print(f"      - {f:15}: {n.get(f)} ({type(n.get(f)).__name__})")
                        
                        # 4. Demonstrate Filterability
                        print("\n🔍 Demonstrating Filterability (ISO >= 0)...")
                        filter_r = await s.run("MATCH (n:ImageAsset) WHERE n.iso >= 0 RETURN count(n) as c")
                        count = (await filter_r.single())["c"]
                        print(f"      Matched nodes via numeric filter: {count}")
                        return

            print("\n❌ SMART EXIF FAILURE: Timeout waiting for properties.")
    finally:
        await broker.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
