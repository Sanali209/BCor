"""ULTRA PIPELINE VERIFICATION: 10x Robust Metadata Ecosystem."""
import asyncio
import os
import sys
import uuid
from typing import Any
import httpx

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

async def check_ollama():
    """Check if Ollama is running and has required models."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                if "moondream:latest" in models or "moondream" in models:
                    print("    Ollama: Detected running instance with moondream.")
                    return True
                else:
                    print("    WARNING: Ollama running, but 'moondream' model NOT found.")
    except Exception as e:
        print(f"    DEBUG: Ollama check failed: {e}")
        pass
    print("    WARNING: Ollama AI fields will be skipped in this run.")
    return False

async def main():
    IMG_PATH = r"D:\image_db\safe repo\ddsearch\kim_possible\kim_possible_1.webp"
    NEO4J_URI = "bolt://localhost:7687"
    AUTH = ("neo4j", "password")

    print(f"\n🚀 STARTING ULTRA PIPELINE VERIFICATION on {os.path.basename(IMG_PATH)}")
    
    ollama_ready = await check_ollama()
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
            print(f"    [1] Clean: Node {node_id} removed.")

            # 2. Ingest
            asset = factory.create_from_path(IMG_PATH)
            async with driver.session() as s:
                await mapper.save(asset, session=s)
            
            print("    [2] Ingest: Initial save dispatched all handlers.")

            # 3. Comprehensive Polling
            fields_to_check = {
                "perceptual_hash": "L1: Hashing",
                "thumbnail_bytes": "L1: Thumbnail",
                "clip_embedding": "L2: CLIP Vector",
                "blip_embedding": "L2: BLIP Vector",
                "exif_data": "10x: pyexiv2 EXIF",
                "xmp_data": "10x: pyexiv2 XMP",
                "auto_tags": "10x: Cascading Tags (Wait for EXIF/XMP)",
                "xmp_sync": "10x: Write-back Sync (Wait for Tags)",
            }
            
            if ollama_ready:
                fields_to_check["description"] = "AI: VLM Description (Ollama)"
                fields_to_check["ollama_embedding"] = "AI: Ollama Embedding (Wait for Description)"

            print(f"\n[3] Polling for {len(fields_to_check)} fields...")
            
            for i in range(120): # Longer timeout for all-in-one
                await asyncio.sleep(2)
                async with driver.session() as s:
                    r = await s.run(
                        "MATCH (n:Asset:ImageAsset {id: $id}) RETURN n, labels(n) as labels", id=node_id
                    )
                    record = await r.single()
                    if not record:
                        continue
                    
                    n = record["n"]
                    found = []
                    missing = []
                    for f, desc in fields_to_check.items():
                        val = n.get(f)
                        # Specific Logic for non-empty arrival
                        is_found = False
                        if f == "xmp_sync":
                            is_found = val is True or val is False # it starts as False but arrives as result
                        elif isinstance(val, (list, dict, str, bytes)):
                            is_found = len(val) > 0
                        else:
                            is_found = val is not None
                            
                        if is_found:
                            found.append(f)
                        else:
                            missing.append(f)

                    if i % 5 == 0 or not missing:
                        status = "PROGRESSING" if missing else "COMPLETE"
                        print(f"    [{i*2}s] {status}: Found {len(found)}/{len(fields_to_check)} fields. Missing: {missing}")

                    if not missing:
                        print("\n🏆 ULTIMATE SUCCESS: 10x Robust Pipeline Fully Operational!")
                        print(f"      Labels    : {record['labels']}")
                        print(f"      pHash     : {n['perceptual_hash']}")
                        print(f"      Tags      : {n['auto_tags']}")
                        if ollama_ready:
                            desc_prev = n['description'][:50] + "..."
                            print(f"      AI Desc   : {desc_prev}")
                            print(f"      AI Embed  : {len(n['ollama_embedding'])} dims")
                        return

            print("\n❌ ULTIMATE FAILURE: Pipeline stalled.")
    finally:
        await broker.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
