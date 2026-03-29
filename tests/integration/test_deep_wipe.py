import pytest
import asyncio
import os
from unittest.mock import MagicMock, AsyncMock
from neo4j import AsyncGraphDatabase
import pytest_asyncio
from src.apps.asset_explorer.presentation.viewmodels.explorer import AssetExplorerViewModel
from src.modules.assets.domain.models import Asset, InferenceEvent
from src.modules.assets.domain.services import AssetIngestionService
from src.modules.agm.mapper import AGMMapper

@pytest_asyncio.fixture
async def neo4j_session():
    uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    auth = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
    async with AsyncGraphDatabase.driver(uri, auth=auth) as driver:
        async with driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
            yield session

@pytest.mark.asyncio
async def test_deep_wipe_clears_all_nodes(neo4j_session):
    # Setup: Create an asset and an orphaned inference event
    await neo4j_session.run("CREATE (:Asset {id: 'test-asset-1', name: 'Test'})")
    await neo4j_session.run("CREATE (:InferenceEvent {id: 'event-1', handler_name: 'pyexiv2'})")
    
    # Verify they exist
    result = await neo4j_session.run("MATCH (n) RETURN count(n) as count")
    record = await result.single()
    assert record["count"] == 2
    
    # Initialize VM with mocks
    mapper = MagicMock(spec=AGMMapper)
    ingestion = MagicMock(spec=AssetIngestionService)
    driver = MagicMock()
    driver.session = lambda: neo4j_session # Reuse the test session fixture wrapper if it supports it, 
                                           # but neo4j_session is an actual session. 
                                           # We need a driver that returns this session.
    
    class MockDriver:
        def __init__(self, sess): self.sess = sess
        def session(self): return self.sess

    # Re-wrap session to act like a context manager for the driver
    class AsyncSessionCM:
        def __init__(self, sess): self.sess = sess
        async def __aenter__(self): return self.sess
        async def __aexit__(self, *args): pass

    class MockDriverCM:
        def __init__(self, sess): self.sess = sess
        def session(self): return AsyncSessionCM(self.sess)

    vm = AssetExplorerViewModel(mapper, ingestion, MockDriverCM(neo4j_session))
    
    # Execute Deep Wipe
    await vm.clear_database()
    
    # Verify DB is empty
    result = await neo4j_session.run("MATCH (n) RETURN count(n) as count")
    record = await result.single()
    assert record["count"] == 0
    
    # Verify ingestion was stopped
    ingestion.stop_ingestion.assert_called_once()

@pytest.mark.asyncio
async def test_deep_wipe_updates_ui_state(neo4j_session):
    mapper = MagicMock(spec=AGMMapper)
    ingestion = MagicMock(spec=AssetIngestionService)
    
    class AsyncSessionCM:
        def __init__(self, sess): self.sess = sess
        async def __aenter__(self): return self.sess
        async def __aexit__(self, *args): pass
    class MockDriverCM:
        def __init__(self, sess): self.sess = sess
        def session(self): return AsyncSessionCM(self.sess)

    vm = AssetExplorerViewModel(mapper, ingestion, MockDriverCM(neo4j_session))
    vm._results = [Asset(id="123", uri="file://test")]
    
    results_emitted = []
    vm.results_updated.connect(lambda r: results_emitted.append(r))
    
    await vm.clear_database()
    
    assert vm.results == []
    assert len(results_emitted) > 0
    assert results_emitted[-1] == []
