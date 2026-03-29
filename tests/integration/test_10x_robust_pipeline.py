"""OMNIBUS VERIFICATION: 10x Robust Assets Pipeline."""
import asyncio
import os
import sys
import uuid
import time
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

    print(f"\n🚀 OMNIBUS 10x PIPELINE VERIFICATION on {os.path.basename(IMG_PATH)}")
    
    # 0. Startup Infrastructure
    await broker.startup()
    
    try:
        container = make_async_container(_AppProvider(), AssetsInfrastructureProvider())
        bus = await container.get(MessageBus)
        bus.register_event(StoredFieldRecalculationRequested, handle_stored_field_recalc)
        
        mapper = AGMMapper(container=container, message_bus=bus)
        factory = AssetFactory()

        async with AsyncGraphDatabase.driver(NEO4J_URI, auth=AUTH) as driver:
            node_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"file://{IMG_PATH}"))
            
            # 1. CLEAN START
            async with driver.session() as s:
                await s.run("MATCH (n {id: $id}) DETACH DELETE n", id=node_id)
            print("    [1] Environment: Clean state established.")

            # 2. FACTORY INGESTION (Dimensions Verification)
            asset = factory.create_from_path(IMG_PATH)
            print(f"    [2] Ingestion: Factory created {type(asset).__name__}")
            print(f"        -> Dimensions: {asset.width}x{asset.height}")
            
            if asset.width == 0 or asset.height == 0:
                print("    ❌ FAILED: Zero dimensions detected in factory.")
                return

            # 3. SAVE & DISPATCH
            async with driver.session() as s:
                await mapper.save(asset, session=s)
            print("    [3] Mapping: Asset saved to Graph. Background tasks dispatched.")

            # 4. MONITORING OMNIBUS (Polling for ALL metadata)
            check_fields = {
                "Dimensions": ["width", "height"],
                "Smart EXIF": ["captured_at", "camera_make", "iso"],
                "Intelligence": ["description", "ollama_embedding"],
                "Basic": ["perceptual_hash", "thumbnail_bytes"]
            }

            all_required_fields = [f for sublist in check_fields.values() for f in sublist]
            
            print(f"\n[4] Polling for {len(all_required_fields)} robust metadata fields...")
            start_time = time.time()
            
            for i in range(120): # Up to 4 minutes for VLM
                await asyncio.sleep(5)
                async with driver.session() as s:
                    r = await s.run("MATCH (n:ImageAsset {id: $id}) RETURN n", id=node_id)
                    record = await r.single()
                    if not record: continue
                    n = record["n"]
                    
                    found = [f for f in all_required_fields if n.get(f) is not None and str(n.get(f)).strip() not in ("", "0", "0.0", "[]")]
                    
                    elapsed = int(time.time() - start_time)
                    print(f"    [{elapsed}s] Status: {len(found)}/{len(all_required_fields)} ready. Waiting for: {[f for f in all_required_fields if f not in found]}")
                    
                    if len(found) == len(all_required_fields):
                        print("\n🏆 10x PIPELINE SUCCESS! All metadata robustly verified.")
                        print(f"      Width/Height: {n.get('width')}x{n.get('height')}")
                        print(f"      Description : {n.get('description')[:100]}...")
                        print(f"      Embedding   : Detected ({len(n.get('ollama_embedding'))} dimensions)")
                        print(f"      EXIF/Date   : {n.get('captured_at')}")
                        return

            print("\n❌ OMNIBUS TIMEOUT: Some metadata failed to populate.")
            
    finally:
        await broker.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
