import pytest
from unittest.mock import MagicMock, patch
from src.core.system import System
from src.core.messagebus import MessageBus
from src.apps.experemental.imgededupe.module import ImgeDeduplicationModule
from src.apps.experemental.imgededupe.application.messages import (
    StartDeduplicationCommand, DeduplicationStarted, DuplicatesFound,
    StartScanCommand, ScanStarted, ScanCompleted
)
from src.apps.experemental.imgededupe.core.deduper import Deduper

@pytest.mark.asyncio
async def test_handle_start_deduplication():
    # Setup System
    module = ImgeDeduplicationModule()
    system = System(modules=[module])
    await system.start()
    
    # Mock Deduper in the container
    # We want    # Verify that the handler calls deduper.find_duplicates
    container = system.container
    deduper = await container.get(Deduper)
    bus = await container.get(MessageBus)
    
    # Use patch to spy on the deduper instance
    with patch.object(deduper, 'find_duplicates', return_value=[]) as mock_find:
        # Subscribe to events to verify publishing
        events = []
        async def on_event(evt):
            events.append(evt)
            
        bus.register_event(DeduplicationStarted, on_event)
        bus.register_event(DuplicatesFound, on_event)
        
        # Dispatch command
        cmd = StartDeduplicationCommand(
            engine_type="phash",
            threshold=5.0,
            include_ignored=False,
            roots=[]
        )
        
        # We need to implement the handler first for this to even dispatch correctly
        # But in BCor, we usually register handlers in the module
        await bus.dispatch(cmd)
        
        # Verify legacy call
        mock_find.assert_called_once()
        
        # Verify events
        assert len(events) == 2
        assert isinstance(events[0], DeduplicationStarted)
        assert isinstance(events[1], DuplicatesFound)
        assert events[1].relations_count == 0

    await system.stop()

@pytest.mark.asyncio
async def test_handle_start_scan():
    # Setup System
    module = ImgeDeduplicationModule()
    system = System(modules=[module])
    await system.start()
    
    container = system.container
    scanner = await container.get(Scanner)
    bus = await container.get(MessageBus)
    
    with patch.object(scanner, 'scan', return_value=10) as mock_scan:
        events = []
        async def on_event(evt):
            events.append(evt)
        bus.register_event(ScanStarted, on_event)
        bus.register_event(ScanCompleted, on_event)
        
        cmd = StartScanCommand(roots=["/tmp/test"], recursive=True)
        await bus.dispatch(cmd)
        
        mock_scan.assert_called_once_with(roots=["/tmp/test"], recursive=True)
        assert len(events) == 2
        assert isinstance(events[0], ScanStarted)
        assert isinstance(events[1], ScanCompleted)
        assert events[1].files_count == 10

    await system.stop()
