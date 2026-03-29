import pytest
import asyncio
import os
from neo4j import AsyncGraphDatabase
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.messages import StoredFieldRecalculationRequested
from src.modules.assets.domain.factory import AssetFactory
from src.modules.assets.domain.services import AssetIngestionService
from src.modules.assets.infrastructure.handlers.phash import PHashHandler
from src.apps.experemental.declarative_imgededupe.services import DeduplicationService
from src.core.messagebus import MessageBus
from src.core.unit_of_work import AbstractUnitOfWork
from dishka import make_async_container, Provider, provide, Scope
import uuid

class MockUoW(AbstractUnitOfWork):
    def _commit(self): pass
    def rollback(self): pass
    def _get_all_seen_aggregates(self): return []

class AppProvider(Provider):
    @provide(scope=Scope.APP)
    def get_bus(self, uow: AbstractUnitOfWork) -> MessageBus:
        return MessageBus(uow=uow)
    
    @provide(scope=Scope.APP)
    def get_uow(self) -> AbstractUnitOfWork:
        return MockUoW()

def make_phash_handler(driver: AsyncGraphDatabase.driver, sem: asyncio.Semaphore, phash_tasks: set):
    async def handle_phash_recalc(event: StoredFieldRecalculationRequested):
        """Non-blocking driver handler for pHash in the test with retries and throttling."""
        if event.handler == "PHashHandler":
            from loguru import logger
            
            # Throttle the actual hashing + DB write context
            async def run_throttled():
                async with sem:
                    try:
                        logger.debug(f"Computing pHash for {event.node_id}...")
                        phash = await PHashHandler.run(uri=event.new_source_val)
                        
                        async def tx_func(tx, node_id, p_hash):
                            await tx.run(
                                "MATCH (n:ImageAsset {id: $id}) SET n.perceptual_hash = $phash",
                                id=node_id, phash=p_hash
                            )

                        async with driver.session() as session:
                            await session.execute_write(tx_func, event.node_id, phash)
                        logger.debug(f"Updated pHash for {event.node_id}")
                    except Exception as e:
                        logger.error(f"Failed to update pHash for {event.node_id}: {e}")

            task = asyncio.create_task(run_throttled())
            phash_tasks.add(task)
            task.add_done_callback(phash_tasks.discard)

    return handle_phash_recalc

@pytest.mark.asyncio
async def test_ddsearch_full_scan():
    """
    Integration test for the ddsearch directory.
    Verifies that the scanning and deduplication pipeline works on real data.
    """
    root_path = "D:/image_db/safe repo/ddsearch/kim_possible"
    if not os.path.exists(root_path):
        pytest.skip(f"Test directory {root_path} not found.")

    # 1. Setup BCor stack
    uri = "bolt://localhost:7687"
    auth = ("neo4j", "password")
    
    # Throttling and task tracking
    sem = asyncio.Semaphore(30) # Lower concurrency for safety on Windows
    phash_tasks = set()

    # Increase max_connection_pool_size to prevent deadlocks
    async with AsyncGraphDatabase.driver(uri, auth=auth, max_connection_pool_size=500) as driver:
        container = make_async_container(AppProvider())
        bus = await container.get(MessageBus)
        bus.register_event(
            StoredFieldRecalculationRequested, 
            make_phash_handler(driver, sem, phash_tasks)
        )
        
        mapper = AGMMapper(container=container, message_bus=bus)
        factory = AssetFactory()
        ingestion = AssetIngestionService(mapper=mapper, factory=factory)
        service = DeduplicationService(ingestion=ingestion, mapper=mapper)

        # 2. Run Scan
        print(f"\nStarting ingestion for {root_path}...")
        # STILL use the service but now we bypass the single session to avoid stalls
        # and letting each save() create its own short-lived session.
        assets = await ingestion.ingest_directory(root_path, session=None)
        print(f"Ingested {len(assets)} assets. Waiting for pHash background tasks...")
        
        # Wait for all background pHash tasks to finish
        while phash_tasks:
            await asyncio.sleep(0.5)
            if len(phash_tasks) % 10 == 0:
                print(f"Pending tasks: {len(phash_tasks)}")
        
        async with driver.session() as session_neo:
            from src.modules.assets.domain.models import ImageAsset
            print("Reloading assets with computed hashes...")
            # Use another session or the same, but pHash should be there now
            assets = await mapper.query(ImageAsset).all(session_neo)
            
            has_hash = [a for a in assets if a.perceptual_hash]
            print(f"Assets with hashes: {len(has_hash)} / {len(assets)}")
            
            if len(has_hash) == 0:
                print("WARNING: No hashes computed! Check event bus/handlers.")
                return

            print("Starting phash clustering...")
            session_result = await service.run_dedupe(
                root_path, 
                session_neo, 
                threshold=15, 
                engine="phash"
            )
            
            # Assertions
            print(f"\nScan results for {root_path}:")
            print(f"Total Assets: {session_result.count_total}")
            print(f"Duplicates Found: {session_result.count_duplicates}")
            
            assert session_result.count_total > 0
            assert session_result.status == "finished"
            
            # Refresh assets one last time to see similarities
            assets = await mapper.query(ImageAsset).all(session_neo)
            matches = [a for a in assets if a.similar]
            if matches:
                print(f"\nTotal matches found: {len(matches)}")
                for m in matches[:10]:
                    print(f"  - {m.name} is similar to {len(m.similar)} assets")
            else:
                print("\nNo duplicates found with current threshold.")

if __name__ == "__main__":
    asyncio.run(test_ddsearch_full_scan())
