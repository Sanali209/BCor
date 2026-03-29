"""Verification script for full asset metadata extraction."""
import asyncio
import os
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uuid
from loguru import logger
from neo4j import AsyncGraphDatabase
from typing import TYPE_CHECKING, Annotated, Any, Optional
from dishka import make_async_container, Provider, provide, Scope

from src.core.messagebus import MessageBus
from src.core.unit_of_work import AbstractUnitOfWork
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.handlers import handle_stored_field_recalc
from src.modules.agm.messages import StoredFieldRecalculationRequested
from src.modules.assets.domain.factory import AssetFactory
from src.modules.assets.infrastructure.providers import AssetsInfrastructureProvider
from src.adapters.taskiq_broker import broker

# --- DI Setup ---

class _MockUoW(AbstractUnitOfWork):
    def _commit(self): pass
    def rollback(self): pass
    def _get_all_seen_aggregates(self): return []

class _AppProvider(Provider):
    @provide(scope=Scope.APP)
    def get_uow(self) -> AbstractUnitOfWork:
        return _MockUoW()
    @provide(scope=Scope.APP)
    def get_bus(self, uow: AbstractUnitOfWork) -> MessageBus:
        return MessageBus(uow=uow)
    
    # Injected dependencies for handlers
    @provide(scope=Scope.APP)
    def get_registry(self) -> Any:
        return AssetsInfrastructureProvider().provide_handler_registry()

# --- Verification Logic ---

async def main():
    IMG_PATH = "D:/image_db/safe repo/ddsearch/kim_possible/kim_possible_1.webp"
    URI = "bolt://localhost:7687"
    AUTH = ("neo4j", "password")

    print(f"\n[1] Setup: {os.path.basename(IMG_PATH)}")
    
    # 0. Start TaskIQ Broker
    await broker.startup()
    
    try:
        container = make_async_container(_AppProvider())
        bus = await container.get(MessageBus)
        bus.register_event(StoredFieldRecalculationRequested, handle_stored_field_recalc)
        
        mapper = AGMMapper(container=container, message_bus=bus)
        factory = AssetFactory()

        async with AsyncGraphDatabase.driver(URI, auth=AUTH) as driver:
            # Clear specific node
            node_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"file://{IMG_PATH}"))
            async with driver.session() as s:
                await s.run("MATCH (n {id: $id}) DETACH DELETE n", id=node_id)
            
            print(f"    Node {node_id} cleared from DB.")

            # 2. Ingest
            asset = factory.create_from_path(IMG_PATH)
            async with driver.session() as s:
                # This triggers events via mapper Side Effects
                await mapper.save(asset, session=s)
            
            print("    Asset ingested. Recalculation events dispatched (TaskIQ).")

            # 3. Poll for results
            print("\n[2] Polling Neo4j for metadata (timeout=120s)...")
            fields_to_check = [
                "perceptual_hash", 
                "thumbnail_bytes", 
                "clip_embedding", 
                "blip_embedding", 
                "exif_data",
                "auto_tags"
            ]
            
            for i in range(60):
                await asyncio.sleep(2)
                async with driver.session() as s:
                    r = await s.run(
                        "MATCH (n:ImageAsset {id: $id}) RETURN n", id=node_id
                    )
                    record = await r.single()
                    if not record:
                        print(f"    [{i*2}s] Node not found yet...")
                        continue
                    
                    n = record["n"]
                    found = []
                    missing = []
                    for f in fields_to_check:
                        val = n.get(f)
                        # For auto_tags, we accept empty list if it exists in the node
                        if f == "auto_tags" and val is not None:
                            found.append(f)
                        elif val is not None and (not isinstance(val, (list, str, bytes, dict)) or len(val) > 0):
                            found.append(f)
                        else:
                            missing.append(f)
                    
                    if i % 5 == 0 or not missing:
                        print(f"    [{i*2}s] Status: Found={found} | Missing={missing}")
                    
                    if not missing:
                        print("\n✅ SUCCESS: All metadata captured!")
                        # Detailed check
                        print(f"      pHash     : {n['perceptual_hash']}")
                        print(f"      Thumbnail : {len(n['thumbnail_bytes'])} bytes")
                        print(f"      CLIP      : {len(n['clip_embedding'])} dims")
                        print(f"      Tags      : {n['auto_tags']}")
                        return

            print("\n❌ TIMEOUT: Some fields never updated.")
    finally:
        await broker.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
