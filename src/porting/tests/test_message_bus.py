import pytest
import asyncio
from SLM.appGlue.DesignPaterns.MessageSystem import MessageSystem
from bubus import EventBus
from src.modules.sanali.events import LegacyMessageEvent
from src.core.testing import BCorTestSystem

@pytest.mark.asyncio
async def test_message_bus_bridge():
    """
    Verify that SendMessage on legacy MessageSystem reaches BCor bubus.
    """
    manifest = "src/apps/experemental/sanali/Python/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        # Register bridge and get bus
        from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
        container = get_service_container()
        await container.prepare_bcor_bridge()
        
        bus = await system.container.get(EventBus)
        
        # Track received messages
        received = []
        
        async def handler(event):
            received.append(event)
        
        # Subscribe to ALL legacy messages via BCor bus
        bus.on(LegacyMessageEvent, handler)
        
        # Send legacy message (which is sync)
        MessageSystem.SendMessage("TestMessage", data="payload")
        
        # Give it a tiny bit of time for async dispatch
        await asyncio.sleep(0.2)
        
        assert len(received) == 1
        assert received[0].message_name == "TestMessage"
        assert received[0].message_data == {"data": "payload"}
